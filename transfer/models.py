from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Club(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="社團名稱")
    max_participants = models.IntegerField(verbose_name="人數上限")
    founder = models.ForeignKey(User, on_delete=models.SET_NULL, null = True,related_name='founded_clubs', verbose_name="社長")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null = True, related_name='taught_clubs', verbose_name="指導老師")

    def current_participants(self):
        return self.user_set.count()  # 假設User有old_club字段其實我也不太清楚這行要幹嘛

    def is_full(self):
        return self.current_participants() >= self.max_participants

    def __str__(self):
        return self.name

class TransferRequest(models.Model):
    STATUS_CHOICES = [
        (0, '原社長審核中'),
        (1, '原老師審核中'),
        (2, '新社長審核中'),
        (3, '新老師審核中'),
        (4, '完成'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfer_requests', verbose_name="申請人")
    old_club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='outgoing_requests', verbose_name="原社團")
    new_club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='incoming_requests', verbose_name="新社團")
    status = models.IntegerField(choices=STATUS_CHOICES, default=0, verbose_name="進度狀態")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="申請時間")

    def submission_number(self):
        # ai給的建議:遞交編號可以用created_at的timestamp或id
        return self.id

    def queue_position(self):
        # ai給的建議:新社團排隊人數：計算status < 4的申請數
        return TransferRequest.objects.filter(new_club=self.new_club, status__lt=4).count()

    def __str__(self):
        return f"{self.student.username} 從 {self.old_club} 到 {self.new_club}"

class User(models.Model):
    username =models.CharField('用戶姓名', max_length=50)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_set', verbose_name="目前社團")
    def __str__(self):
        return self.username
    
