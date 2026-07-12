from fastapi import FastAPI #type:ignore[import]
import sentry_sdk #type: ignore[import]
import uvicorn

sentry_sdk.init(
    dsn="https://330342688da39bc5c169d52346daf352@o4511528701329408.ingest.de.sentry.io/4511528709062736",
    send_default_pii=True,
    environment=...,
    debug=... 
)

app = FastAPI(
    title=...,
    description=...,
    version=...,
    environment=...,
    license_info = {
        "name": "Proprietary License",
    },
    contact={
        "name": "Biswadeep Tewari",
        "email": "[EMAIL_ADDRESS]",
        "phone": ...,
    },
    
)

@app.on_event('startup')
async def startup_event():
    print('Application is firing up ')

@app.on_event('shutdown')
async def shutdown_event():
    print('Application is shutting down ')
    


if __name__ == '__main__':
    import sys
    import os
    
    # Add the root project directory so uvicorn's reloader can find 'src'
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    os.environ["PYTHONPATH"] = root_dir + os.pathsep + os.environ.get("PYTHONPATH", "")
    uvicorn.run('src.backend.api.main:app', port=8000, reload=True)