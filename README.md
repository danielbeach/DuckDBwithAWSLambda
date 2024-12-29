### DuckDB + AWS Lambda

This repo goes along with a Substack post that explores using
`DuckDB` with `DeltaLake` on an AWS `Lambda`.

https://dataengineeringcentral.substack.com/p/aws-lambda-duckdb-and-delta-lake

#### To build and deploy the Docker image to ECR for Lambda ...
```
docker build \
  --build-arg AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  --build-arg AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  --platform linux/amd64 \
  -t duckdelta .
```

To drop into that Docker container ...
```
docker run -it duckdelta . /bin/bash
```

To tag and push an image ...
```
docker tag duckdelta 992921014520.dkr.ecr.us-east-1.amazonaws.com/duckdelta/docker:latest
docker push 992921014520.dkr.ecr.us-east-1.amazonaws.com/duckdelta/docker:latest
```

#### Create the Delta Lake tables on S3
Next, I wanted to create the Delta Lake tables on s3 that 
our AWS Lambda will interact with. See `create_delta_tables.py` for
the code used to do that. Uses `dask` and a sample dataset.


#### Lambda code to read and write the S3 Delta Tables (DuckDB and DeltaLake)
There is some code located in `lambda_function.py` that shows who you can
read, write, and transform data with `duckdb` and `deltalake` Python packages,
also using `pyarrow` datasets as the go-between.

#### Lambda setup
You need to have a working ECR Registry created for the Docker image.

