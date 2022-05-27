import uvicorn

# TODO make sure configuration is valid, if not create configured minio bucket and mongo database

if __name__ == '__main__':
    uvicorn.run('mds.app:app', host='localhost', port=8000, reload=True)
