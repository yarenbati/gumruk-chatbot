"""Build and validate the retrieval-blind M12D candidate; never freeze it."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.source_identity import DocumentSourceKey

DOC = "5607_kacakcilikla_mucadele_kanunu"
ROWS = [
  [
    "5607 say\u0131l\u0131 Kanunun amac\u0131 nedir; hangi fiilleri, yapt\u0131r\u0131mlar\u0131 ve hangi usul ve esaslar\u0131 belirlemeyi hedefler?",
    "1",
    "direct_provision",
    "easy",
    "Madde 1 f\u0131kra 1: ka\u00e7ak\u00e7\u0131l\u0131k fiilleri, yapt\u0131r\u0131mlar ve \u00f6nleme, izleme, ara\u015ft\u0131rma usul ve esaslar\u0131."
  ],
  [
    "5607 say\u0131l\u0131 Kanunda \u201cg\u00fcmr\u00fcklenmi\u015f de\u011fer\u201d nas\u0131l tan\u0131mlan\u0131r ve ithal ve ihra\u00e7 e\u015fyas\u0131 bak\u0131m\u0131ndan hangi de\u011ferlerin toplam\u0131 esas al\u0131n\u0131r?",
    "2",
    "definition",
    "easy",
    "Madde 2 f\u0131kra 1(b): ithalde CIF, ihracatta FOB k\u0131ymetine g\u00fcmr\u00fck vergileri eklenir."
  ],
  [
    "E\u015fyan\u0131n g\u00fcmr\u00fck i\u015flemlerine tabi tutulmadan \u00fclkeye sokulmas\u0131 hangi hapis ve adl\u00ee para cezas\u0131n\u0131 gerektirir; e\u015fya g\u00fcmr\u00fck kap\u0131lar\u0131 d\u0131\u015f\u0131ndan sokulursa ceza nas\u0131l de\u011fi\u015fir?",
    "3",
    "penalty",
    "medium",
    "Madde 3 f\u0131kra 1: temel hapis/adl\u00ee para cezas\u0131 ve kap\u0131 d\u0131\u015f\u0131ndan giri\u015f art\u0131r\u0131m\u0131."
  ],
  [
    "\u0130hracat ger\u00e7ekle\u015fmedi\u011fi h\u00e2lde ger\u00e7ekle\u015fmi\u015f gibi g\u00f6sterilmesi veya ihra\u00e7 mal\u0131n\u0131n cins, miktar, evsaf ya da fiyat\u0131n\u0131n de\u011fi\u015ftirilmesi hangi yapt\u0131r\u0131mla kar\u015f\u0131lan\u0131r; beyandaki fark y\u00fczde onu a\u015fm\u0131yorsa hangi i\u015flem uygulan\u0131r?",
    "3",
    "exception_condition",
    "hard",
    "Madde 3 f\u0131kra 9: te\u015fvik, s\u00fcbvansiyon veya parasal iade amac\u0131yla yap\u0131lan fiiller ve y\u00fczde onu a\u015fmayan fark istisnas\u0131."
  ],
  [
    "Ulusal marker seviyenin alt\u0131nda olan veya hi\u00e7 marker i\u00e7ermeyen akaryak\u0131t bak\u0131m\u0131ndan hangi ticari fiiller su\u00e7 kapsam\u0131ndad\u0131r ve hangi yapt\u0131r\u0131m \u00f6ng\u00f6r\u00fcl\u00fcr?",
    "3",
    "penalty",
    "hard",
    "Madde 3 f\u0131kra 11(a-c): ticari \u00fcretim, bulundurma, nakil, sat\u0131\u015f ve bilerek sat\u0131n alma; ceza ve ka\u00e7ak giri\u015f istisnas\u0131."
  ],
  [
    "Ka\u00e7ak\u00e7\u0131l\u0131k su\u00e7unun te\u015febb\u00fcs a\u015famas\u0131nda kalmas\u0131 h\u00e2linde 5607 say\u0131l\u0131 Kanun bak\u0131m\u0131ndan nas\u0131l cezaland\u0131rma yap\u0131l\u0131r?",
    "3",
    "direct_provision",
    "easy",
    "Madde 3 f\u0131kra 22: te\u015febb\u00fcste kalan fiiller tamamlanm\u0131\u015f gibi cezaland\u0131r\u0131l\u0131r."
  ],
  [
    "Ka\u00e7ak\u00e7\u0131l\u0131k su\u00e7unun bir \u00f6rg\u00fct\u00fcn faaliyeti \u00e7er\u00e7evesinde veya \u00fc\u00e7 ya da daha fazla ki\u015fi taraf\u0131ndan birlikte i\u015flenmesi h\u00e2linde cezalar nas\u0131l art\u0131r\u0131l\u0131r?",
    "4",
    "condition",
    "medium",
    "Madde 4 f\u0131kra 1-2: \u00f6rg\u00fct faaliyeti ve en az \u00fc\u00e7 ki\u015finin birlikte i\u015flemesi i\u00e7in farkl\u0131 art\u0131r\u0131mlar."
  ],
  [
    "Etkin pi\u015fmanl\u0131k g\u00f6steren ki\u015fi, resm\u00ee makamlar haber almadan \u00f6nce hangi bilgileri verirse ve bu bilgi neyi sa\u011flarsa cezaland\u0131r\u0131lmaz?",
    "5",
    "condition",
    "medium",
    "Madde 5 f\u0131kra 1: fiil, failler ve saklama yerlerinin bildirimi; yakalama veya e\u015fyan\u0131n ele ge\u00e7irilmesi sonucu."
  ],
  [
    "Yolcunun \u00fczerinde, e\u015fyas\u0131 aras\u0131nda veya ta\u015f\u0131ma arac\u0131nda beyan\u0131na ayk\u0131r\u0131 olarak \u00e7\u0131kan e\u015fya hangi iki durumda 3 \u00fcnc\u00fc madde h\u00fck\u00fcmlerine tabi olur?",
    "6",
    "exception_condition",
    "medium",
    "Madde 6 f\u0131kra 4: ticari mahiyet veya ithal/ihracat yasa\u011f\u0131; at\u0131f yap\u0131lan maddenin yapt\u0131r\u0131m\u0131 sorulmuyor."
  ],
  [
    "\u0130zinsiz olarak g\u00fcmr\u00fck b\u00f6lgesine girip sahile veya ba\u015fka bir gemiye yana\u015fan geminin kaptan\u0131 hangi ek bulgular varsa ka\u00e7ak\u00e7\u0131l\u0131k h\u00fck\u00fcmlerine g\u00f6re cezaland\u0131r\u0131l\u0131r?",
    "7",
    "condition",
    "hard",
    "Madde 7 f\u0131kra 1: ge\u00e7erli mazeret yoklu\u011fu ve yasak ya da ta\u015f\u0131ma/y\u00fckleme belgelerinde yer almayan e\u015fya."
  ],
  [
    "Ka\u00e7ak e\u015fya, silah, m\u00fchimmat, patlay\u0131c\u0131 veya uyu\u015fturucu bulundu\u011fundan \u015f\u00fcphe edilen kap, ambalaj, ta\u015f\u0131ma arac\u0131 ve ki\u015filer \u00fczerindeki arama ve elkoyma hangi kanuna g\u00f6re yap\u0131l\u0131r?",
    "9",
    "procedural_rule",
    "easy",
    "Madde 9 f\u0131kra 1: 5271 say\u0131l\u0131 Ceza Muhakemesi Kanununa at\u0131f; d\u0131\u015f kanunun ayr\u0131nt\u0131lar\u0131 sorulmuyor."
  ],
  [
    "Ka\u00e7ak\u00e7\u0131l\u0131k su\u00e7lar\u0131nda kullan\u0131lan ta\u015f\u0131ta hangi \u015fartlarda elkonulur ve elkonulan ta\u015f\u0131t\u0131n m\u00fcsadere edilebilmesi bak\u0131m\u0131ndan hangi ba\u011flant\u0131l\u0131 durumlar \u00f6nem ta\u015f\u0131r?",
    "10,13",
    "procedural_condition",
    "hard",
    "Madde 10 f\u0131kra 1-2 elkoyma ve al\u0131koymay\u0131; Madde 13 f\u0131kra 1(a-c) ba\u011f\u0131ms\u0131z m\u00fcsadere ko\u015fullar\u0131n\u0131 verir. Biri \u00e7\u0131kar\u0131l\u0131rsa iki a\u015famadan biri cevaps\u0131z kal\u0131r."
  ],
  [
    "Ka\u00e7ak \u015f\u00fcphesiyle elkonulan e\u015fya ile al\u0131konulan ta\u015f\u0131tlar\u0131n g\u00fcmr\u00fck idaresine tesliminde hangi ay\u0131rt edici bilgileri i\u00e7eren tutanak d\u00fczenlenir?",
    "11",
    "procedural_rule",
    "medium",
    "Madde 11 f\u0131kra 1: miktar, cins, marka, tip, model, seri numaras\u0131 gibi ay\u0131r\u0131c\u0131 bilgiler."
  ],
  [
    "Yabanc\u0131 \u00fclkeden gelen yasak e\u015fya y\u00fckleme veya ta\u015f\u0131ma belgelerinde g\u00f6sterilerek g\u00fcmr\u00fc\u011fe getirilmi\u015fse hangi g\u00fcvenlik ko\u015fullar\u0131 alt\u0131nda nereye g\u00f6nderilebilir?",
    "12",
    "procedural_condition",
    "medium",
    "Madde 12 f\u0131kra 1: teminat ve g\u00fcvenlik tedbirleriyle geldi\u011fi yere veya di\u011fer \u00fclkeye iade/sevk."
  ],
  [
    "Ka\u00e7ak e\u015fya ta\u015f\u0131mas\u0131nda bilerek kullan\u0131lan bir ta\u015f\u0131t\u0131n m\u00fcsadere edilebilmesi i\u00e7in 5607 say\u0131l\u0131 Kanunda \u00f6ng\u00f6r\u00fclen ko\u015fullardan hangileri vard\u0131r?",
    "13",
    "confiscation",
    "hard",
    "Madde 13 f\u0131kra 1(a-c): gizli tertibat, y\u00fck\u00fcn miktar/hacim a\u011f\u0131rl\u0131\u011f\u0131 veya arac\u0131n gereklili\u011fi, yasak/zararl\u0131 e\u015fya. Sicile kay\u0131tl\u0131 olmama bu maddenin ko\u015fulu de\u011fildir."
  ],
  [
    "M\u00fcsadere yapt\u0131r\u0131m\u0131n\u0131n uygulanabilece\u011fi e\u015fyan\u0131n tasfiyesi bak\u0131m\u0131ndan, ka\u00e7ak akaryak\u0131t d\u0131\u015f\u0131ndaki e\u015fya i\u00e7in temel s\u00fcre ve istisnai h\u0131zland\u0131rma ko\u015fullar\u0131 nelerdir?",
    "16",
    "procedural_condition",
    "hard",
    "Madde 16 f\u0131kra 1: alt\u0131 ay i\u00e7inde karar; zarar, esasl\u0131 de\u011fer kayb\u0131 tehlikesi veya ciddi muhafaza k\u00fclfetinde bir ay; s\u00fcresinde karar yoksa derhal tasfiye."
  ],
  [
    "Elkonulan ve teknik d\u00fczenlemelere uygun ka\u00e7ak akaryak\u0131t\u0131n hangi kurumlar taraf\u0131ndan, hangi y\u00f6ntemlerle tasfiye edilmesi \u00f6ng\u00f6r\u00fcl\u00fcr?",
    "16/A",
    "authority_responsibility",
    "hard",
    "Madde 16/A f\u0131kra 1: il \u00f6zel idaresi/Y\u0130KOB ve hudut kap\u0131lar\u0131nda g\u00fcmr\u00fck idaresi; bedelsiz tahsis veya sat\u0131\u015f ve numune h\u00fck\u00fcmleri."
  ],
  [
    "5607 say\u0131l\u0131 Kanun kapsam\u0131ndaki su\u00e7lar nedeniyle a\u00e7\u0131lan davalara hangi mahkemeler bakar; resm\u00ee belgede sahtecilik ba\u011flant\u0131s\u0131 varsa g\u00f6revli mahkeme nas\u0131l de\u011fi\u015fir?",
    "17",
    "authority_responsibility",
    "medium",
    "Madde 17 f\u0131kra 2: belirlenen asliye ceza mahkemeleri; ba\u011flant\u0131l\u0131 resm\u00ee belgede sahtecilikte a\u011f\u0131r ceza."
  ],
  [
    "Ka\u00e7ak\u00e7\u0131l\u0131k fiillerini \u00f6nleme, izleme ve ara\u015ft\u0131rma y\u00fck\u00fcml\u00fcl\u00fc\u011f\u00fc hangi kamu g\u00f6revlileri ve kurum personeline verilmi\u015ftir?",
    "19",
    "authority_responsibility",
    "medium",
    "Madde 19 f\u0131kra 1: m\u00fclk\u00ee amirler, G\u00fcmr\u00fck M\u00fcste\u015farl\u0131\u011f\u0131, Emniyet, Jandarma ve Sahil G\u00fcvenlik personeli; kaynakta yaz\u0131l\u0131 kurum adlar\u0131 korunur."
  ],
  [
    "Ka\u00e7ak\u00e7\u0131l\u0131k fiillerinin izlenmesine ili\u015fkin tutanakta olay ve kan\u0131tlar ile elkonulan e\u015fya ve ta\u015f\u0131ma ara\u00e7lar\u0131 hakk\u0131nda hangi ayr\u0131nt\u0131lar bulunmal\u0131d\u0131r?",
    "20",
    "procedural_rule",
    "hard",
    "Madde 20 f\u0131kra 1(b): olay/kan\u0131t, t\u00fcr, kapsam, miktar, nitelik ve nerede/nas\u0131l elkonuldu\u011fu."
  ],
  [
    "5607 say\u0131l\u0131 Kanun \u00e7er\u00e7evesindeki kontroll\u00fc teslimat i\u015flemlerini hangi kurumlar y\u00fcr\u00fct\u00fcr?",
    "21",
    "authority_responsibility",
    "easy",
    "Madde 21 f\u0131kra 1: G\u00fcmr\u00fck M\u00fcste\u015farl\u0131\u011f\u0131, Emniyet, Jandarma ve Sahil G\u00fcvenlik; d\u0131\u015f kanunun usul ayr\u0131nt\u0131lar\u0131 sorulmuyor."
  ],
  [
    "G\u00fcmr\u00fck kap\u0131lar\u0131 ve yollar\u0131 d\u0131\u015f\u0131ndan g\u00fcmr\u00fck b\u00f6lgesine girmek isteyen ki\u015fi \u201cdur\u201d uyar\u0131s\u0131na uymazsa, silah kullanma yetkisi bak\u0131m\u0131ndan kanun hangi a\u015famal\u0131 uyar\u0131y\u0131 \u00f6ng\u00f6r\u00fcr?",
    "22",
    "procedural_condition",
    "medium",
    "Madde 22 f\u0131kra 1: dur uyar\u0131s\u0131 ve havaya ate\u015fle yineleme; me\u015fru m\u00fcdafaa ayr\u0131ca d\u00fczenlenir."
  ],
  [
    "Ka\u00e7ak \u015f\u00fcphesiyle e\u015fya yakalanmas\u0131 h\u00e2linde muhbir ve elkoyma ikramiyesine hak kazananlara \u00f6deme yap\u0131lmas\u0131n\u0131n temel dayana\u011f\u0131 nedir?",
    "23",
    "authority_responsibility",
    "medium",
    "Madde 23 f\u0131kra 1-2: ikramiyenin esaslar\u0131, hak sahipleri ve payla\u015f\u0131m; kaynak maddenin belirlenmesi ama\u00e7lan\u0131r."
  ],
  [
    "Ka\u00e7ak\u00e7\u0131l\u0131k fiillerinin \u00f6nlenmesi, izlenmesi ve ara\u015ft\u0131r\u0131lmas\u0131 i\u00e7in kriminal laboratuvarlar\u0131 hangi kurum kurar ve \u00e7al\u0131\u015fma usul ve esaslar\u0131n\u0131 kim belirler?",
    "24",
    "authority_responsibility",
    "easy",
    "Madde 24 f\u0131kra 1: G\u00fcmr\u00fck M\u00fcste\u015farl\u0131\u011f\u0131 kurar ve y\u00f6netmelikle \u00e7al\u0131\u015fma usul ve esaslar\u0131n\u0131 belirler."
  ],
  [
    "E\u015fyay\u0131 g\u00fcmr\u00fck i\u015flemlerine tabi tutmaks\u0131z\u0131n \u00fclkeye sokan ki\u015fi i\u00e7in Madde 3 f\u0131kra 1'deki temel yapt\u0131r\u0131m nedir; ayn\u0131 su\u00e7 \u00f6rg\u00fct faaliyeti \u00e7er\u00e7evesinde i\u015flenirse ve e\u015fya toplum sa\u011fl\u0131\u011f\u0131n\u0131 tehdit edecek nitelikteyse Madde 4 f\u0131kra 1 ve 7 hangi ek sonu\u00e7lar\u0131, hangi ko\u015fulla \u00f6ng\u00f6r\u00fcr?",
    "3,4",
    "multi_part",
    "hard",
    "Madde 3(1): bir-be\u015f y\u0131l hapis ve on bin g\u00fcne kadar adl\u00ee para cezas\u0131. Madde 4(1),(7): \u00f6rg\u00fct art\u0131r\u0131m\u0131 ve daha a\u011f\u0131r su\u00e7 olu\u015fmamas\u0131 ko\u015fuluyla on y\u0131ll\u0131k hapis alt s\u0131n\u0131r\u0131. Temel yapt\u0131r\u0131m yaln\u0131z 3'te, ek sonu\u00e7lar yaln\u0131z 4'tedir; her iki kaynak zorunludur."
  ],
  [
    "E\u015fyay\u0131 g\u00fcmr\u00fck i\u015flemlerine tabi tutmaks\u0131z\u0131n \u00fclkeye sokman\u0131n Madde 3 f\u0131kra 1'deki temel yapt\u0131r\u0131m\u0131 nedir; Madde 5 kapsam\u0131nda etkin pi\u015fmanl\u0131kla \u00f6deme yap\u0131l\u0131rsa \u00f6deme tutar\u0131, soru\u015fturma ve kovu\u015fturma evrelerindeki indirimler ve bu imk\u00e2ndan yararlanamayan h\u00e2ller nelerdir?",
    "3,5",
    "multi_part",
    "hard",
    "Madde 3(1) temel hapis/adl\u00ee para cezas\u0131n\u0131 verir. Madde 5(2)(a-b),(3) iki kat g\u00fcmr\u00fcklenmi\u015f de\u011fer \u00f6demesini, yar\u0131/\u00fc\u00e7te bir indirimlerini ve m\u00fckerrir/\u00f6rg\u00fct istisnalar\u0131n\u0131 verir. Biri olmadan temel yapt\u0131r\u0131m veya indirim ko\u015fullar\u0131 eksik kal\u0131r."
  ],
  [
    "Ka\u00e7ak \u015f\u00fcphesiyle elkonulan e\u015fyan\u0131n g\u00fcmr\u00fck idaresine tesliminde Madde 11'e g\u00f6re tutanakta hangi ay\u0131r\u0131c\u0131 bilgiler bulunmal\u0131d\u0131r; ayr\u0131ca ka\u00e7ak akaryak\u0131t d\u0131\u015f\u0131ndaki e\u015fya i\u00e7in Madde 16'da tasfiye karar\u0131 verilmesinin temel s\u00fcresi ve bu s\u00fcrede karar verilmemesinin sonucu nedir?",
    "11,16",
    "multi_part",
    "hard",
    "Madde 11(1): miktar, cins, marka, tip, model, seri numaras\u0131. Madde 16(1): temel alt\u0131 ayl\u0131k karar s\u00fcresi ve s\u00fcresinde karar yoksa derhal tasfiye. Teslim kayd\u0131 ile tasfiye s\u00fcresi ayr\u0131 alt sorulard\u0131r; her kaynak kendi alt sorusu i\u00e7in zorunludur."
  ],
  [
    "16/A ve 23 \u00fcnc\u00fc maddelerde belirtilen y\u00f6netmeliklerin y\u00fcr\u00fcrl\u00fc\u011fe konulmas\u0131 i\u00e7in Ge\u00e7ici Madde 7 hangi s\u00fcreyi \u00f6ng\u00f6r\u00fcr?",
    "g7",
    "long_tail",
    "medium",
    "Ge\u00e7ici Madde 7(1), 16/A(6) ve 23(5-6) at\u0131flar\u0131 ile alt\u0131 ayl\u0131k s\u00fcreyi kendisi i\u00e7erir. Yaln\u0131z s\u00fcre soruldu\u011fu i\u00e7in at\u0131f yap\u0131lan maddeler gerekli gold de\u011fildir."
  ],
  [
    "Madde 3 f\u0131kra 2 hangi fiili ve yapt\u0131r\u0131m\u0131 d\u00fczenler; g\u00fcmr\u00fck vergilerinin k\u0131smen eksik \u00f6denmesi nedeniyle a\u00e7\u0131lm\u0131\u015f kamu davalar\u0131nda, Ge\u00e7ici Madde 10'un y\u00fcr\u00fcrl\u00fc\u011f\u00fcnden \u00f6nce elkonulan ve m\u00fcsadere karar\u0131 verilmemi\u015f kara ta\u015f\u0131tlar\u0131n\u0131n iadesi i\u00e7in bu ge\u00e7ici h\u00fck\u00fcm hangi ba\u015fvuru, \u00f6deme ve tasfiye ko\u015fullar\u0131n\u0131 arar?",
    "3,g10",
    "multi_part",
    "hard",
    "Madde 3(2): aldat\u0131c\u0131 i\u015flem/davran\u0131\u015fla vergileri k\u0131smen veya tamamen \u00f6demeden giri\u015f ve cezas\u0131. Ge\u00e7ici 10(1)(a-b): tasfiye tamamlanmam\u0131\u015f olmal\u0131; izleyen alt\u0131nc\u0131 ay sonuna kadar ba\u015fvuru ve ba\u015fvurudan bir ay i\u00e7inde ilk iktisap \u00d6TV'sinin %25'i \u00f6deme. Fiil/yapt\u0131r\u0131m 3'ten, ge\u00e7i\u015f ko\u015fullar\u0131 Ge\u00e7ici 10'dan gelir."
  ],
  [
    "Madde 5 f\u0131kra 2(b) uyar\u0131nca kovu\u015fturma evresinde hangi \u00f6deme kar\u015f\u0131l\u0131\u011f\u0131nda ne oranda ceza indirimi uygulan\u0131r; Ge\u00e7ici Madde 12 f\u0131kra 1 bu imk\u00e2n\u0131 h\u00fck\u00fcm verilmi\u015f ve dosyas\u0131 infaz a\u015famas\u0131ndaki ki\u015filere hangi \u00f6deme ve ge\u00e7ici s\u00fcre ko\u015fullar\u0131yla tan\u0131r?",
    "5,g12",
    "multi_part",
    "hard",
    "Madde 5(2)(b): h\u00fckme kadar iki kat g\u00fcmr\u00fcklenmi\u015f de\u011fer \u00f6demesi ve \u00fc\u00e7te bir indirim. Ge\u00e7ici 12(1): infaz a\u015famas\u0131ndaki ki\u015filer i\u00e7in y\u00fcr\u00fcrl\u00fckten itibaren doksan g\u00fcn i\u00e7inde ayn\u0131 \u00f6deme. \u0130ndirim oran\u0131 5'te, infaz a\u015famas\u0131na ge\u00e7i\u015f ve s\u00fcre Ge\u00e7ici 12'dedir; iki kaynak zorunludur."
  ]
]

def main() -> None:
    """Validate admitted sources, build candidates, and verify serialized outputs."""
    assert Path(__file__).read_bytes().isascii(), "Builder must remain ASCII-only"
    base = ROOT / "data/processed/5607-kacakcilikla-mucadele-kanunu"
    articles = json.loads(Path(str(base) + ".articles.json").read_text(encoding="utf-8"))
    chunks = json.loads(Path(str(base) + ".chunks.json").read_text(encoding="utf-8"))
    assert articles["document_id"] == chunks["document_id"] == DOC
    assert articles["article_count"] == len(articles["articles"]) == 43
    assert chunks["chunk_count"] == len(chunks["chunks"]) == 46
    lookup = {(a["article_type"], a["article_no"]): a for a in articles["articles"]}
    assert len(lookup) == 43
    questions = []
    for i, (question, refs, category, difficulty, notes) in enumerate(ROWS, 1):
        sources = []
        sections = []
        for ref in refs.split(","):
            kind, number = ("gecici", ref[1:]) if ref.startswith("g") else ("normal", ref)
            article = lookup[(kind, number)]
            assert article["document_id"] == DOC and article["text"].strip()
            DocumentSourceKey(DOC, kind, number)
            sources.append(dict(document_id=DOC, article_type=kind, article_no=number))
            if article["section_context"] not in sections:
                sections.append(article["section_context"])
            assert any(c["article_id"] == article["article_id"] for c in chunks["chunks"])
        questions.append(dict(id=f"k5607-{i:03d}", question=question,
            expected_sources=sources, expected_document_ids=[DOC], category=category,
            difficulty=difficulty, source_verified=True, notes=notes,
            section_context=" | ".join(sections)))
    assert len(questions) == 30
    assert len({q["id"] for q in questions}) == 30
    assert len({q["question"].casefold() for q in questions}) == 30
    payload = dict(source_identity_schema="document-source-v1", questions=questions)
    candidate = ROOT / "evaluation/questions_5607.candidate.json"
    review = ROOT / "reports/evaluation/m12d-5607-question-review.csv"
    # Validate before writes and again after parsing the output.
    audit = validate(payload)
    with candidate.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=True, indent=2)
        handle.write("\n")
    parsed = json.loads(candidate.read_text(encoding="utf-8"))
    assert parsed == payload and validate(parsed) == audit
    assert candidate.read_bytes().isascii()
    fields = ["id", "question", "expected_sources", "category", "difficulty",
              "source_verified", "multi_source", "section_context", "review_status", "reviewer_notes"]
    with review.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for q in parsed["questions"]:
            writer.writerow({**{k: q[k] for k in ["id", "question", "category", "difficulty",
                "source_verified", "section_context"]},
                "expected_sources": " | ".join(str(DocumentSourceKey(**s)) for s in q["expected_sources"]),
                "multi_source": len(q["expected_sources"]) > 1,
                "review_status": "pending", "reviewer_notes": ""})
    with review.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 30
    for q, row in zip(questions, rows):
        assert row["question"] == q["question"]
        assert row["section_context"] == q["section_context"]
        assert row["review_status"] == "pending" and row["reviewer_notes"] == ""
    print(json.dumps(audit, ensure_ascii=True, sort_keys=True))

def validate(payload: dict) -> dict:
    """Reject damaged parsed strings and invalid coverage before publication."""
    questions = payload["questions"]
    strings = "\n".join(q["question"] + "\n" + q["notes"] + "\n" + q["section_context"] for q in questions)
    replacement = strings.count("\ufffd")
    mojibake = sum(strings.count(chr(n)) for n in [0xc3, 0xc4, 0xc5, 0xc2])
    inside = sum(s[i-1].isalpha() and s[i+1].isalpha()
        for s in [q["question"] + " " + q["notes"] for q in questions]
        for i in range(1, len(s)-1) if s[i] == "?")
    assert replacement == mojibake == inside == 0
    assert all(q["question"].count("?") == 1 and q["question"].endswith("?") for q in questions)
    assert all("?" not in q["notes"] + q["section_context"] for q in questions)
    words = ["say\u0131l\u0131","ka\u00e7ak\u00e7\u0131l\u0131k","g\u00fcmr\u00fck","g\u00fcmr\u00fcklenmi\u015f","e\u015fya","f\u0131kra","B\u00f6l\u00fcm","m\u00fcsadere","yapt\u0131r\u0131m","G\u00fcmr\u00fck M\u00fcste\u015farl\u0131\u011f\u0131"]
    assert all(w in strings for w in words)
    keys = {DocumentSourceKey(**s) for q in questions for s in q["expected_sources"]}
    assert all(k.document_id == DOC and k.article_type in {"normal", "gecici"} for k in keys)
    sections = set(s for q in questions for s in q["section_context"].split(" | "))
    assert len(sections) == 5
    multi = sum(len(q["expected_sources"]) > 1 for q in questions)
    temporary = sum(any(s["article_type"] == "gecici" for s in q["expected_sources"]) for q in questions)
    assert multi == 6 and temporary == 3
    sets = [tuple(sorted(str(DocumentSourceKey(**s)) for s in q["expected_sources"])) for q in questions]
    return dict(questions=30, distinct_keys=len(keys),
        normal_keys=sum(k.article_type == "normal" for k in keys),
        gecici_keys=sum(k.article_type == "gecici" for k in keys),
        suffixed_keys=sum("/" in k.article_no for k in keys),
        multi_source_questions=multi, gecici_questions=temporary,
        sections=sorted(sections), duplicate_exact_questions=0,
        duplicate_expected_source_sets=len(sets)-len(set(sets)),
        replacement_characters=replacement, mojibake=mojibake,
        question_mark_inside_words=inside, malformed_source_keys=0,
        source_verified_false=sum(q["source_verified"] is not True for q in questions))

if __name__ == "__main__":
    main()
