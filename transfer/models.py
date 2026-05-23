from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class Club(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="社團名稱")
    max_participants = models.IntegerField(verbose_name="人數上限")
    founder = models.ForeignKey(User, on_delete=models.SET_NULL, null = True,related_name='founded_clubs', verbose_name="社長")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null = True, related_name='taught_clubs', verbose_name="指導老師")
    description = models.TextField(max_length=200, unique=True, verbose_name="社團介紹", blank=True, null=True)

    def save(self, *args, **kwargs): #每次儲存Club時都能自動更新社長的UserProfile
        super().save(*args, **kwargs)
        if self.founder:
            try:
                profile = self.founder.profile
                # 如果他原本檔案記錄的社團不等於這間社團，就強制校正
                if profile.club != self:
                    profile.club = self
                    profile.save()
            except Exception:
                # 用 except 預防萬一：如果該 User（例如大系統管理員）沒有 UserProfile，就跳過
                pass
    
    def current_participants(self):
        return self.members.count()  # 假設User有old_club字段

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

class UserProfile(models.Model):
    # 透過 OneToOneField 將這個表跟 Django 內建的 User 綁定在一起
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="使用者帳號")
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='members', verbose_name="目前社團")
    def __str__(self):
        return self.user.username
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    
