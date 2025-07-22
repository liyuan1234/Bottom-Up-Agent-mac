from typing import Union, Dict
import os
import warnings

class Logger:
    supported_backends = ['wandb']  

    def __init__(self, project_name, experiment_name, backend='wandb', config=None):
        assert backend in self.supported_backends, f"Backend '{backend}' is not supported."
        self.backend = backend
        self.logger = None

        if backend == 'wandb':
            import wandb
            WANDB_API_KEY = os.environ.get("WANDB_API_KEY", None)
            if WANDB_API_KEY:
                wandb.login(key=WANDB_API_KEY)
            wandb.init(project=project_name, id=experiment_name, resume='allow', config=config)
            self.logger = wandb


    def log(self, data: Union[str, Dict], step=None):
        if self.backend == 'wandb':
            if isinstance(data, str):
                self.logger.termlog(data)    
            elif isinstance(data, dict):
                self.logger.log(data, step=step)
                
    def log_image(self, image, caption=""):
        if self.backend == 'wandb':
            self.logger.log({"image": self.logger.Image(image, caption=caption)})

    def log_video(self, video_path, caption=""):
        if self.backend == 'wandb':
            self.logger.log({"video": self.logger.Video(video_path, caption=caption)})

    def last_value(self, key):
        if self.backend == 'wandb':
            return self.logger.run.summary.get(key, None)

    def finish(self):
        if self.backend == 'wandb':
            self.logger.finish()
