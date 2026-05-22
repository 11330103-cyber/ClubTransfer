from django.shortcuts import render, redirect ,get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import TransferRequest, Club, UserProfile


def detail(request):
    clubs = Club.objects.all()
    return render(request, 'transfer/detail.html', {'clubs': clubs})


def index(request):
    return render(request, 'transfer/index.html')

@login_required
def apply_transfer(request):
    clubs = Club.objects.all()

    #自動抓取該學生目前的社團
    try:
        current_club = request.user.profile.club
    except:
        current_club = None 

    if request.method == 'POST':  
        new_club_id = request.POST.get('new_club')

        if not current_club:
            return render(request, 'transfer/apply.html', {'error': '您目前沒有所屬社團，無法申請轉社。', 'current_club': current_club, 'clubs': clubs})
        
        if not new_club_id:
            return render(request, 'transfer/apply.html', {'error': '請選擇新社團。', 'clubs': clubs, 'current_club': current_club})
            
        try:
            new_club = Club.objects.get(id=new_club_id)
        except Club.DoesNotExist:
            return render(request, 'transfer/apply.html', {'error': '選擇的社團不存在。', 'clubs': clubs, 'current_club': current_club})

        if TransferRequest.objects.filter(student=request.user, status__lt=4).exists():
            return render(request, 'transfer/apply.html', {'error': '您已有正在審核中的轉社申請，請勿重複申請！', 'clubs': clubs, 'current_club': current_club})

        if new_club.is_full():
            return render(request, 'transfer/apply.html', {'error': '社團已滿！', 'clubs': clubs, 'current_club': current_club})

        TransferRequest.objects.create(student=request.user, old_club=current_club, new_club=new_club)
        return redirect('progress')

    return render(request, 'transfer/apply.html', {'clubs': clubs, 'current_club': current_club})

@login_required
def progress(request):
    user = request.user
    if user.is_staff or user.is_superuser:#判斷如果是「學務處 / 最高管理員」，可以直接看到所有的申請單
        requests = TransferRequest.objects.all()

    else:   #如果是一般登入者（可能是學生、社長、或老師）
        # 使用 Q 物件進行「或 (OR)」的查詢
        requests = TransferRequest.objects.filter(
            Q(student=user) |                  # 條件A: 申請人
            Q(old_club__founder=user) |        # 條件B: 「原社團」的社長
            Q(new_club__founder=user) |        # 條件C: 「新社團」的社長
            Q(old_club__teacher=user) |        # 條件D: 「原社團」的指導老師
            Q(new_club__teacher=user)          # 條件E: 「新社團」的指導老師
        ).distinct()  # distinct() 用來避免重複抓取同一筆資料
    #requests = TransferRequest.objects.filter(student=request.user)
    return render(request, 'transfer/progress.html', {'requests': requests})

# 這裡目前只列出學生自己的申請進度。後面再加上社長老師學務處的額外過濾權限TAT

@login_required
def pending_approvals(request):
    user = request.user

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')  # 抓取按鈕的 value ('approve' 或 'reject')
        
        # 抓出這張申請單
        transfer_request = get_object_or_404(TransferRequest, id=request_id)
        
        # 權限檢查，確認登入者此時此到底有沒有資格動這張單子
        is_old_founder = (transfer_request.status == 0 and transfer_request.old_club.founder == user)
        is_old_teacher = (transfer_request.status == 1 and transfer_request.old_club.teacher == user)
        is_new_founder = (transfer_request.status == 2 and transfer_request.new_club.founder == user)
        is_new_teacher = (transfer_request.status == 3 and transfer_request.new_club.teacher == user)
        
        if not (is_old_founder or is_old_teacher or is_new_founder or is_new_teacher):
            return HttpResponseForbidden("您目前沒有權限審核這筆表單，或者還沒輪到您。")
        
        if action == 'approve':
            if is_old_founder:
                transfer_request.status = 1
            elif is_old_teacher:
                transfer_request.status = 2
            elif is_new_founder:
                transfer_request.status = 3
            elif is_new_teacher:
                transfer_request.status = 4
                # 最終通過，更新學生的Profile
                student_profile = transfer_request.student.profile
                student_profile.club = transfer_request.new_club
                student_profile.save()
            transfer_request.save()
            
        elif action == 'reject':
            #拒絕，直接將這筆申請單從資料庫刪除
            transfer_request.delete()
            
        return redirect('pending_approvals')

    # ─── 【GET 處理階段】：單純進入網頁時，列出「輪到我審核」的申請單 ───
    pending_requests = TransferRequest.objects.filter(
        Q(status=0, old_club__founder=user) |  # 輪到我這個「原社長」
        Q(status=1, old_club__teacher=user) |  # 輪到我這個「原老師」
        Q(status=2, new_club__founder=user) |  # 輪到我這個「新社長」
        Q(status=3, new_club__teacher=user)    # 輪到我這個「新老師」
    ).distinct()

    return render(request, 'transfer/approve.html', {'requests': pending_requests})


