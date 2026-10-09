import re

with open("yonetim/templates/yonetim/urun_islemleri.html", "r", encoding="utf-8") as f:
    content = f.read()

# Update select options
content = content.replace("Satış Yap (Alacak Oluşturur)", "Satış Yap (Satış Fişi Oluşturur)")
content = content.replace("Alış Yap (Ödeme Oluşturur)", "Alış Yap (Alış Fişi Oluşturur)")

# Update history table links
history_links = """
                        <form action="{% url 'yonetim:fis_durum_degistir' islem.id %}" method="post" style="display:inline;">
                            {% csrf_token %}
                            <input type="hidden" name="next" value="{{ request.path }}">
                            <button type="submit" class="btn btn-sm btn-outline-secondary" style="padding:2px 5px; font-size:12px;">Durum</button>
                        </form>
                        <a href="{% url 'yonetim:fis_duzenle' islem.id %}" class="btn btn-sm btn-outline-primary" style="padding:2px 5px; font-size:12px; margin-left: 5px;">Düzenle</a>
                        <form action="{% url 'yonetim:fis_sil' islem.id %}" method="post" style="display:inline;" onsubmit="return confirm('Silmek istediğinize emin misiniz?');">
                            {% csrf_token %}
                            <input type="hidden" name="next" value="{{ request.path }}">
                            <button type="submit" class="btn btn-sm btn-outline-danger" style="padding:2px 5px; font-size:12px; margin-left: 5px;">Sil</button>
                        </form>
"""

# I will just replace the whole {% if islem.tur == 'Satış (Alacak)' %} block with the Fis links
# because for both sales and purchases, it's a Fis.

table_block_start = content.find("{% if islem.tur == 'Satış (Alacak)' %}")
table_block_end = content.find("{% endif %}", table_block_start) + len("{% endif %}")

if table_block_start != -1 and table_block_end != -1:
    content = content[:table_block_start] + history_links.strip() + content[table_block_end:]

with open("yonetim/templates/yonetim/urun_islemleri.html", "w", encoding="utf-8") as f:
    f.write(content)
