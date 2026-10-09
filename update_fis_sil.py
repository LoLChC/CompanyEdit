import re

with open("yonetim/views.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace return redirect('yonetim:fis_liste') with return redirect(request.META.get('HTTP_REFERER', 'yonetim:fis_liste'))
# inside fis_sil function
def_sil_start = content.find("def fis_sil(request, pk):")
if def_sil_start != -1:
    end_of_func = content.find("def cari_sil(request, pk):", def_sil_start)
    func_content = content[def_sil_start:end_of_func]
    
    new_func_content = func_content.replace(
        "return redirect('yonetim:fis_liste')",
        "return redirect(request.POST.get('next') or request.META.get('HTTP_REFERER', 'yonetim:fis_liste'))"
    )
    
    content = content[:def_sil_start] + new_func_content + content[end_of_func:]
    
with open("yonetim/views.py", "w", encoding="utf-8") as f:
    f.write(content)
