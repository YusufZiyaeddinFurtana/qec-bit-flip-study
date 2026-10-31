# Bu projeyi sonradan öğrenmek için kısa rehber

Bu depo, standart üç qubit bit-flip kodunun yeniden üretimidir. Aşağıdaki sıra,
çalışmayı anlamanı ve daha sonra kendi deneylerini eklemeni kolaylaştırır.

## 1. Önce iki grafiği oku

README'deki ilk grafikte yatay eksen, her fiziksel qubitin X hatası yaşama
olasılığı. Dikey eksen, düzeltmeden sonra kalan mantıksal X hatasının olasılığı.
Kesikli çizgi korumasız durumu, renkli çizgi teoriyi, noktalar simülasyonu gösteriyor.

`p = 0.10` örneğinde korumasız hata olasılığı %10. İdeal kodun teorik sonucu
%2,8. Gerçek simülasyon sayımı `results/summary.md` içinde; tam olarak %2,8
olması gerekmiyor. Rastgele denemelerin sayısı sonlu.

İkinci grafikte X yerine Z hataları uygulanıyor; kod ve düzeltme değişmiyor.
Aynı p için mantıksal Z hatası %24,4. Bu deneyde faz değişimine duyarlı `|+>`
başlangıç durumu kullanılıyor. Yalnızca `|0>` ile deneseydik faz hatasını bu
şekilde göremezdik.

## 2. İki ve üç hatanın neden sorun olduğunu anla

`0 -> 000`, `1 -> 111`. `000 -> 010` olduğunda tek hatayı düzeltebilirsin.
`000 -> 110` olduğunda aynı düzeltme kuralı yanlış mantıksal sonuca gider.

İki hatanın olasılığı `3 p² (1-p)`, üç hatanınki `p³`. İlk formülün toplamı
bu yüzden `3 p² (1-p) + p³`. Başındaki 3, iki hata için üç farklı yerleşimden
geliyor. Bu sonuç bağımsız, aynı olasılıklı hataları varsayıyor.

Z hataları için tek veya üç hata mantıksal fazı değiştirir. Bu da
`3 p (1-p)² + p³` sonucunu verir. İki Z hatasının etkileri kod uzayında birbirini
götürür.

## 3. Kuantum kısmını ayırt et

Bir kuantum durumu `alpha|0> + beta|1>` ise kodlama
`alpha|000> + beta|111>` üretir. Bilinmeyen durumun üç bağımsız kopyasını
oluşturmaz.

Veri qubitlerini tek tek ölçmek süperpozisyonu bozabilir. Bunun yerine iki
parite bilgisi ölçülür: `q0 XOR q1`, `q1 XOR q2`. Buna **syndrome** denir.
Depoda qubit sırası soldan sağa `|q0 q1 q2>` olarak tanımlı.

| Syndrome | Uygulanan düzeltme |
|---|---|
| 00 | İşlem yapma |
| 10 | q0 üzerine X |
| 11 | q1 üzerine X |
| 01 | q2 üzerine X |

Bu tablo tek X hatası veya hatasız durum için doğru düzeltmeyi seçer. Daha
çok X hatasında yanlış bir düzeltme seçebilir. Z hataları ise bu iki pariteyi
değiştirmez.

`qec_study/model.py` bu parite ölçümlerini projektörlerle hesaplıyor. Yardımcı
qubitlerin kapılarını tek tek simüle etmiyor; ideal ölçümün veri qubitlerine
etkisini modelliyor. Ölçüm dalları yoğunluk matrisiyle birleştiriliyor.

## 4. Kodu şu sırayla oku

1. `experiment.py` içindeki `count_errors`: rastgele fiziksel hatalar üretir.
2. `model.py` içindeki `logical_error_theory`: teorik formülleri verir.
3. `model.py` içindeki `encode`, `syndrome_projector`, `recovery_density`:
   kuantum durumuna ne olduğunu hesaplar.
4. `logical_output`: sekiz hata örüntüsünü olasılıklarıyla tam olarak toplar.
5. `tests/test_model.py`: süperpozisyonun korunduğuna ve formüllere bakar.

İstatistiksel örnekleme ve kuantum hesabı aynı sonuca iki farklı yoldan gider.
Örnekleme doğrudan teorik mantıksal hata olasılığından sayı çekmez; fiziksel
qubitlerin hata maskelerini üretir.

## 5. Belirsizliği doğru yorumla

Her noktada 200.000 korumalı ve ayrıca 200.000 korumasız deney var. Hata
çubukları %95 Wilson aralıkları. Bunlar tüm grafik için ortak bir garanti
değil; her nokta için ayrı bir belirsizlik hesabı. Bir aralığın teoriyi
kaçırması tek başına kodun bozuk olduğunu göstermez. Hiç hata gözlenmese bile
gerçek hata olasılığının sıfır olduğunu söyleyemeyiz.

## 6. Hazır olduğunda yapabileceğin ilk değişiklik

README'deki kurulumdan sonra şunu çalıştır:

```bash
python -m qec_study --shots 500000 --seed 17 --output alternate-run
```

Yeni sonuçlar ayrı klasöre yazılır. Noktaların ve aralıkların nasıl değiştiğine
bak; deneme sayısı arttıkça tek bir tahminin teoriye her seferinde yaklaşması
gerekmez, ancak tipik belirsizlik küçülür.

## Hocayla konuşmadan önce cevaplayabilmen gereken sorular

- Formüldeki `3` nereden geliyor?
- Hangi hata türü düzeltiliyor, hangisi düzeltilmiyor?
- Neden veri qubitlerini doğrudan ölçmüyoruz?
- Faz deneyinde neden `|+>` kullanıyoruz?
- Modelde hangi işlemler kusursuz kabul edildi?
- Noktalar teoriye neden tam oturmuyor?
- Bu sonuçlar gerçek donanım hakkında hangi soruları henüz cevaplamıyor?

Araştırma görüşmesi öncesinde bu soruları cevaplayabilmen iyi bir hazırlık
eşiği olur.

Temel kaynak: [IBM Quantum — Repetition codes](https://quantum.cloud.ibm.com/learning/en/courses/foundations-of-quantum-error-correction/correcting-quantum-errors/repetition-codes).
