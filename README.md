# Maismaasõidukite tehnoülevaatused Eestis (2023) - ETL Pipeline ja Visualiseerimine
Projekt on **ETL-pipeline**, mis ekstraktib, puhastab ja laadib andmed SQLite andmebaasi ning genereerib visualiseerimise RMarkdowni abil. Selleks kasutab projekt Andmete teabevärava andmestiku ["Maismaasõidukite tehnoülevaatused Eestis"](https://andmed.eesti.ee/datasets/maismaasoidukite-tehnoulevaatused-eestis) andmed aastast **2023**.

Andmestiku API: https://andmed.eesti.ee/api/datasets/ae47fec7-63d0-4b7a-969b-fbdfed21d52a/files/1943aed4-8e53-4e70-9946-7fc8ad1f7dfe/download-s3
## Arhitektuur
Pipeline on rakendatud Docker konteineris ning koosneb:

-- Python skriptid (5 tk)

-- operations.json (OpenRefine'i tegevuste fail)

-- RMarkdown fail (analysis.Rmd)

- **pipeline.py**
    - täidab orkestreerija rolli
    - Jooksutab skripte järjekorras: **download_csv.py -> clean_csv.py -> csv_to_sqlite.py -> render_report.py**
- **download_csv.py** 
    - "Extract" osa ETL-st
    - laeb alla toores CSV faili Andme teabevärava andmebaasist kasutades nende API
    - Kasutab Pythoni *requests* sõltuvust, et allalaadida CSV-t
- **clean_csv.py**
    - "Transform" osa ETL-st
    - Jooksutab konteineri sees OpenRefine'i serverit "headless" režiimis
    - Kasutab OpenRefine'i serverit, et rakendada "operations.json" faili sees olevad puhastustegevused
- **csv_to_sqlite.py**
    - "Load" ja "Transform" osad ETL-st
    - Loob SQLite andmebaasi
    - Loob relatsioonilised tabelid andmebaasis
    - Täidab relatsioonilist andmebaasi  puhastatud CSV faili andmetega
    - Kustutab üksikud NULL kirjed (mis on juba ELT)
- **render_report.py**
    - Käivitab Rscript'i, et renderdada `analysis.Rmd` fail HTML-raportiks ja genereerida visualiseerimise pildid.
    - Salvestab väljundid kausta **reports/output**:
        - **report.html**: lõplik visualiseerimise raport
        - **category_share_pie.png**: sõidukikategooriate osakaal
        - **fail_rate_distribution.png**: ülevaatuspunktide rangeuse jaotus
        - **fail_rate_by_category.png**:rangeus vs kategooria
        - **category_fail_rate.png**: mitte-läbimise määr sõidukikategooriate lõikes

## Eeldused
- Docker
- Docker Compose
- Docker Desktop (**valikuline**)
    - Mugavam konteinerite haldamiseks
- Visual Studio Code koos Remote - Containers laiendusega (**valikuline**)
    - Juhul kui kasutatakse projekti Dev Containerit 
## Paigaldamine
Laadige alla projekt endale sobivasse kausta.
## Kasutamine
Pipeline kasutamiseks on mõeldud 2 peamist varianti.
### 1. Docker Compose
1. Kontrollige, et Docker ja Docker Compose on valmis tööks
2. Avage terminal, CMD või Powershell *pipeline*'i kaustas, kus on **Dockerfile** ja **docker-compose.yml**
3. Kasutage käsku `docker compose up -d` (konteineri ehitamiseks tagataustal) või `docker compose up` (kui soovite näha logisid konteineri kokkupanemisest)
4. Ootage, kuni pipeline automaatselt teeb kõik ära

Antud variant:
 - Teeb läbi kogu ETL protsessi ühe käsuga
 - Salvestab, kasutades *bind mount*e, hostmasinas:
     - **raw_file.csv**: allalaaditud toores CSV
     - **cleaned_file.csv**: puhastatud CSV fail
     - **database.sqlite**: SQLite relatsiooniline andmebaas
     - **report.html**: visualiseerimise raporti
     - Visualiseerimise pildid:
         - **category_share_pie.png**
         - **fail_rate_distribution.png**
         - **fail_rate_by_category.png**
         - **category_fail_rate.png**
### 2. Dev Container (VS Code)
1. Kontrollige, et Docker ja Docker Compose on valmis tööks ning Teil on olemas **Visual Stdio Code** koos **Remote - Containers** laiendusega
2. Avage projekti kaust Visual Studio Code'is
3. Käivitage: `Dev Containers: Rebuild and Open in Container`
4. Ootage, kuni konteiner on valmis
5. Konteineri sees jooksutage...
    5.1. kas `python scripts/pipeline.py`, kui soovite jooksutada kogu pipeline'i koos visualiseerimisega
    5.2. või individuaalsed skriptid, mida soovite kasutada(näiteks ainult download_csv.py ja clean_csv.py)
6. Allalaadige soovitavaid faile enda hostmasinasse. Kõige mugavam viis selleks on vajutada parema hiireklõpsuga failile ja valida "download"

Antud variant:
- Võimaldab töötada otse konteineri sees
- Jooksutada kas kogu *pipeline* või selle osasid endal valikul
- Ei salvesta automaatselt failid hostmasinasse, vaid kasutaja ise peab valima, mida salvestada

## Valmis tulemused
Kaustas "**Project Results and Report**" leiduvad:
- Visualiseerimise raporti
- Visualiseerimise pildid:
    - **category_share_pie.png**
    - **fail_rate_distribution.png**
    - **fail_rate_by_category.png**
    - **category_fail_rate.png**
- Prjekti raport
- PDF dokument "**Andmetehnika mitteinformatikutele - Projekt. 1. osa.
Maismaasõidukite tehnoülevaatused Eestis**", mis kirjeldab OpenRefine'is käsitsi tehtud tegevused, mida salvestati "operations.json" failis
- SQLite andmebaasi Entity-Relationship Diagram
- Projekti ülesehituse diagramm
