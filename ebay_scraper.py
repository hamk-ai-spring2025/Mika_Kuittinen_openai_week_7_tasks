import os
import json
import asyncio
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

# 🔐 Ladataan .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY ei ole asetettu.")

# 🔍 Haetaan tuotetiedot yhdestä eBay-linkistä
async def hae_ebay_tiedot(url):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)

        html = result.html
        if not html:
            raise RuntimeError("HTML-sisältö puuttuu.")

        soup = BeautifulSoup(html, "html.parser")

        # 🔍 Nimi: yritetään <h1><span> tai <h1>
        nimi_elem = soup.select_one("h1 span") or soup.select_one("h1")
        nimi = nimi_elem.text.strip() if nimi_elem else "N/A"

        # 🔍 Hinta: ensin yritetään itemprop, sitten fallback hakusanalla
        hinta_elem = soup.select_one("span[itemprop='price']")
        if not hinta_elem:
            print("⚠️ Ei löytynyt itemprop='price' - haetaan manuaalisesti...")
            for span in soup.find_all("span"):
                txt = span.text.strip()
                if "US $" in txt or "EUR" in txt:
                    print(f"🔍 Löydetty hintateksti: {txt}")
                    hinta_elem = span
                    break
            if not hinta_elem:
                print("❌ Hintaa ei löytynyt.")

        hinta = hinta_elem.text.strip() if hinta_elem else "N/A"

        # 🔍 Arvio (jos saatavilla)
        arvio_elem = soup.select_one("span.review-ratings-cntr span.clrBlack")
        arvio = arvio_elem.text.strip() if arvio_elem else "N/A"

        return {
            "nimi": nimi,
            "kuvaus": "Kuvausta ei saatu sivulta automaattisesti.",
            "hinta": hinta,
            "arvio": arvio,
            "linkki": url
        }

# ✨ GPT-4 parantaa kuvausta
def paranna_kuvaus(tiedot):
    promptti = PromptTemplate.from_template(
        """Sinulle annetaan tuotetiedot. Kirjoita houkutteleva ja sujuva tuotekuvaus suomeksi:

        Tuotenimi: {nimi}
        Kuvaus: {kuvaus}
        Hinta: {hinta}
        Arvostelu: {arvio}

        Parannettu kuvaus:"""
    )
    llm = ChatOpenAI(temperature=0.7, model="gpt-4")
    return (promptti | llm).invoke(tiedot).content.strip()

# 🤝 GPT-vertailu useista tuotteista
def vertaa_tuotteita(tuotteet):
    promptti = PromptTemplate.from_template(
        """Sinulle annetaan useamman tuotteen tiedot. Vertaa tuotteita keskenään ja suosita parasta hinta-laatusuhteen perusteella. Kirjoita suomeksi.

        Tuotteet:
        {tuotteet}

        Yhteenveto:"""
    )
    llm = ChatOpenAI(temperature=0.7, model="gpt-4")
    json_str = json.dumps(tuotteet, ensure_ascii=False, indent=2)
    return (promptti | llm).invoke({"tuotteet": json_str}).content.strip()

# 🧪 Suoritus
if __name__ == "__main__":
    tuotteet = []
    print("Syötä eBay-tuotelinkkejä (tyhjä rivinvaihto lopettaa):")
    while True:
        url = input("Linkki: ").strip()
        if not url:
            break
        if not url.startswith("http") or "ebay.com" not in url:
            print("⛔ Väärän muotoinen linkki, yritä uudelleen.")
            continue
        try:
            tuote = asyncio.run(hae_ebay_tiedot(url))
            tuote["parannettu_kuvaus"] = paranna_kuvaus(tuote)
            tuotteet.append(tuote)
            print(f"✅ Haettu: {tuote['nimi']}")
        except Exception as e:
            print(f"❌ Virhe: {e}")

    if not tuotteet:
        print("⛔ Ei tuotteita käsiteltäväksi.")
        exit()

    # 💾 Tallenna JSON-tiedostoon
    with open("tuotteet.json", "w", encoding="utf-8") as f:
        json.dump(tuotteet, f, ensure_ascii=False, indent=2)
        print("\n💾 Tallennettu tiedostoon tuotteet.json")

    # 📊 Vertailu
    print("\n📊 Vertailu GPT-4:n avulla:\n")
    vertailu = vertaa_tuotteita(tuotteet)
    print(vertailu)