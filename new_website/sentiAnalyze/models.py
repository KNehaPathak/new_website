from django.db import models

# Create your models here.
class Apipasswords(models.Model):
    username = models.CharField(max_length=500)
    key = models.CharField(max_length=500)

    def __str__(self):
        return self.username