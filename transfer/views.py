from django.shortcuts import render, redirect ,get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import TransferRequest, Club, UserProfile


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
def pending_approvals(request): #這裡是社長老師專用的待審核頁面，裡面只會列出「輪到我審核」的申請單
    user = request.user
    
    # 權限過濾：找出「狀態剛好對應到我身分」的申請單
    pending_requests = TransferRequest.objects.filter(
        Q(status=0, old_club__founder=user) |  # 任務 A: 輪到我這個「原社長」審了
        Q(status=1, old_club__teacher=user) |  # 任務 B: 輪到我這個「原老師」審了
        Q(status=2, new_club__founder=user) |  # 任務 C: 輪到我這個「新社長」審了
        Q(status=3, new_club__teacher=user)    # 任務 D: 輪到我這個「新老師」審了
    ).distinct()

    return render(request, 'transfer/approvals.html', {'requests': pending_requests}) 

@login_required
def approve_request(request, request_id):
    # 抓出這張申請單
    transfer_request = get_object_or_404(TransferRequest, id=request_id)
    user = request.user

    if request.method == 'POST':
        # 權限控制與狀態推進邏輯
        if transfer_request.status == 0 and transfer_request.old_club.founder == user:
            transfer_request.status = 1  # 原社長核准 -> 推進給原老師
            
        elif transfer_request.status == 1 and transfer_request.old_club.teacher == user:
            transfer_request.status = 2  # 原老師核准 -> 推進給新社長
            
        elif transfer_request.status == 2 and transfer_request.new_club.founder == user:
            transfer_request.status = 3  # 新社長核准 -> 推進給新老師
            
        elif transfer_request.status == 3 and transfer_request.new_club.teacher == user:
            transfer_request.status = 4  # 新老師核准 -> 流程完成！
            #更新學生的 Profile，把他的 club 換成新社團
            student_profile = transfer_request.student.profile
            student_profile.club = transfer_request.new_club
            student_profile.save()
        else:
            # 拒絕沒有權限審核的用戶，或者還沒輪到他審核
            return HttpResponseForbidden("您目前沒有權限審核這筆表單，或者還沒輪到您審核。")

        # 儲存變更並導向回待辦清單
        transfer_request.save()
        return redirect('pending_approvals')

    # 如果不是 POST 請求，就導回首頁或進度頁
    return redirect('progress')
