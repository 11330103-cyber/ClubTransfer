from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import TransferRequest, Club


def index(request):
    return render(request, 'transfer/index.html')

@login_required
def apply_transfer(request):
    clubs = Club.objects.all()
    if request.method == 'POST':  # 如果是 POST 請求（學生提交表單）
        old_club_id = request.POST.get('old_club')  # 從表單取數據
        new_club_id = request.POST.get('new_club')

        if not old_club_id or not new_club_id:
            return render(request, 'transfer/apply.html', {'error': '請選擇原社團與新社團。', 'clubs': clubs})
        if old_club_id == new_club_id:
            return render(request, 'transfer/apply.html', {'error': '新社團不能和原社團一樣。', 'clubs': clubs})

        try:
            old_club = Club.objects.get(id=old_club_id)
            new_club = Club.objects.get(id=new_club_id)
        except Club.DoesNotExist:
            return render(request, 'transfer/apply.html', {'error': '選擇的社團不存在。', 'clubs': clubs})

        if new_club.is_full():
            return render(request, 'transfer/apply.html', {'error': '社團已滿！', 'clubs': clubs})

        TransferRequest.objects.create(student=request.user, old_club=old_club, new_club=new_club)
        return redirect('progress')

    return render(request, 'transfer/apply.html', {'clubs': clubs})

@login_required
def progress(request):
    requests = TransferRequest.objects.filter(student=request.user)
    return render(request, 'transfer/progress.html', {'requests': requests})

# 這裡目前只列出學生自己的申請進度。後面再加上社長老師學務處的額外過濾權限TAT