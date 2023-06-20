#!/bin/sh

docker network create dask

docker run --network dask --name scheduler -p 8787:8787 -p 8786:8786 --detach mirage dask-scheduler

docker run --network dask --name worker-1 --detach mirage dask-worker scheduler:8786  # start worker
docker run --network dask --name worker-2 --detach mirage dask-worker scheduler:8786  # start worker
docker run --network dask --name worker-3 --detach mirage dask-worker scheduler:8786  # start worker
