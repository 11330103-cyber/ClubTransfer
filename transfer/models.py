from django.db import models
from django.contrib.auth.models import User

class Club(models.Model):
    name = models.CharField('社團名稱', max_length=10)
class TransferRequest(models.Model):
    applicant = models.OneToOneField(User,) 
class User(models.Model):
    student =models.CharField('申請人姓名', max_length=5)