import duckdb
import os
from deltalake import write_deltalake


DELTA_TABLE_PATH = "s3://confessions-of-a-data-guy/ducklamb"
DAILY_TABLE_PATH = "s3://confessions-of-a-data-guy/ducklambcummulative"
KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
SECRET = os.environ["AWS_SECRET_ACCESS_KEY"]


def handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key = event["Records"][0]["s3"]["object"]["key"]

    conn = duckdb.connect()

    conn.query(
        """
               INSTALL httpfs;
               LOAD httpfs;
                CREATE SECRET secretaws (
                TYPE S3,
                PROVIDER CREDENTIAL_CHAIN
            );
               """
    )

    columns_to_keep = """CAST(date as DATE) as date, serial_number, model, capacity_bytes, failure, datacenter,
                       cluster_id, vault_id, pod_id, pod_slot_num"""

    df = conn.query(
        f"""
                    CREATE TABLE data as (
                    SELECT {columns_to_keep} FROM read_csv('s3://{bucket}/{key}', header=true)
                    );
                    SELECT * FROM data;
                    """
    ).arrow()

    write_deltalake(
        DELTA_TABLE_PATH,
        df,
        mode="append",
        storage_options={"AWS_S3_ALLOW_UNSAFE_RENAME": "true"},
    )

    conn.query(
        f"""
                         CREATE TABLE current as (
                        SELECT CAST(date as DATE) date, model, failure_rate
                        FROM delta_scan('{DAILY_TABLE_PATH}')
                        WHERE CAST(date as DATE) IN (SELECT DISTINCT CAST(date as DATE) FROM data)
                        );
                    """
    )

    cummulative_df = conn.query(
        """
                    CREATE TABLE pickles as (
                                  SELECT date, model, failure_rate
                                  FROM current
                                  UNION ALL
                                  SELECT date, model, failure as failure_rate
                                  FROM data
                                  );
                    SELECT CAST(date as STRING) as date, model, CAST(SUM(failure_rate) as INT) as failure_rate
                    FROM pickles
                    GROUP BY date, model;
                                  """
    ).arrow()

    date_partitions = (
        conn.execute("SELECT DISTINCT CAST(date as DATE) date FROM data;")
        .fetchdf()["date"]
        .tolist()
    )
    partition_filters = [("date", "=", x.strftime("%Y-%m-%d")) for x in date_partitions]

    # this eseentially re-writes the partition
    write_deltalake(
        DAILY_TABLE_PATH,
        cummulative_df,
        mode="overwrite",
        partition_filters=partition_filters,
        engine="pyarrow",
        schema_mode="overwrite",
        storage_options={"AWS_S3_ALLOW_UNSAFE_RENAME": "true"},
    )
