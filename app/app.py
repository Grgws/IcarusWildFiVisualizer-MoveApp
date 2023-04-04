from sdk.moveapps_spec import hook_impl
from movingpandas import TrajectoryCollection
import logging
from .IcarusWildFiVisualizer.app import server

class App(object):

    def __init__(self, moveapps_io):
        self.moveapps_io = moveapps_io

    @hook_impl
    def execute(self, data: TrajectoryCollection, config: dict) -> TrajectoryCollection:
        """Start gunicorn server"""

        # Start gunicorn from script (https://docs.gunicorn.org/en/latest/custom.html)
        # Alternatively run gunicorn via this command:
        #   gunicorn -b :8050 app:server --workers 1
        import gunicorn.app.base
        class StandaloneApplication(gunicorn.app.base.BaseApplication):

            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config = {key: value for key, value in self.options.items()
                        if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            'bind': '%s:%s' % ('127.0.0.1', '8050'),
            'workers': 5,
            'reload': True,
        }
        StandaloneApplication(server, options).run()

        return data
