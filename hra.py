import pygame
import random
import sys

pygame.init()
pygame.mixer.init()
SIRKA, VYSKA = 800, 600
screen = pygame.display.set_mode((SIRKA, VYSKA))
pygame.display.set_caption("Trénování reflexů")
pygame.mouse.set_visible(False)

font = pygame.font.Font(None, 40)
mensi_font = pygame.font.Font(None, 30)
velky_font = pygame.font.Font(None, 80)
clock = pygame.time.Clock()

# --- NAČÍTÁNÍ OBRÁZKŮ ---
def nacti_obrazek(cesta, velikost, barva_zaloze):
    try:
        img = pygame.image.load(cesta).convert_alpha()
        return pygame.transform.scale(img, velikost)
    except FileNotFoundError:
        plocha = pygame.Surface(velikost, pygame.SRCALPHA)
        plocha.fill(barva_zaloze)
        return plocha

kurzor_img = nacti_obrazek("zamery.png", (50, 50), (255, 255, 255))

obrazky_zive = {
    "veverka": nacti_obrazek("veverka.png", (100, 100), (0, 255, 0)),
    "krokodyl": nacti_obrazek("krokodyl.png", (100, 100), (0, 100, 0)),
    "banan": nacti_obrazek("banan.png", (100, 100), (255, 255, 0)),
    "izp": nacti_obrazek("izp.png", (100, 100), (0, 0, 255)), 
    "hokej": nacti_obrazek("hokej.png", (100, 100), (255, 255, 255)), 
    "maslo": nacti_obrazek("maslo.png", (100, 100), (210, 105, 30)) 
}

obrazky_mrtve = {
    "veverka": nacti_obrazek("mrtva_veverka.png", (100, 100), (255, 0, 0)),
    "krokodyl": nacti_obrazek("mrtvy_krokodyl.png", (100, 100), (139, 0, 0)),
    "banan": nacti_obrazek("mrtvy_banan.png", (100, 100), (204, 204, 0)),
    "izp": nacti_obrazek("mrtve_izp.png", (100, 100), (0, 0, 139)), 
    "hokej": nacti_obrazek("mrtvy_hokej.png", (100, 100), (200, 200, 200)), 
    "maslo": nacti_obrazek("mrtvy_maslo.png", (100, 100), (139, 69, 19))
}

# --- NAČÍTÁNÍ ZVUKŮ A HUDBY ---
def nacti_zvuk(cesta):
    try: return pygame.mixer.Sound(cesta)
    except FileNotFoundError: return None

zvuky_vystrel = [nacti_zvuk("vystrel1.mp3"), nacti_zvuk("vystrel2.mp3"), nacti_zvuk("vystrel3.mp3")]
zvuk_bod = nacti_zvuk("zvuk_bod.mp3")
zvuk_konec = nacti_zvuk("zvuk_konec.mp3")

zvuky_objeveni = {
    "veverka": [nacti_zvuk("zvuk_veverka1.mp3"), nacti_zvuk("zvuk_veverka2.mp3"), nacti_zvuk("zvuk_veverka3.mp3")],
    "krokodyl": [nacti_zvuk("zvuk_krokodyl1.mp3"), nacti_zvuk("zvuk_krokodyl2.mp3"), nacti_zvuk("zvuk_krokodyl3.mp3")],
    "banan": [nacti_zvuk("zvuk_banan1.mp3"), nacti_zvuk("zvuk_banan2.mp3"), nacti_zvuk("zvuk_banan3.mp3")],
    "izp": [nacti_zvuk("zvuk_izp1.mp3"), nacti_zvuk("zvuk_izp2.mp3"), nacti_zvuk("zvuk_izp3.mp3")],
    "hokej": [nacti_zvuk("zvuk_hokej1.mp3"), nacti_zvuk("zvuk_hokej2.mp3"), nacti_zvuk("zvuk_hokej3.mp3")],
    "maslo": [nacti_zvuk("zvuk_maslo1.mp3"), nacti_zvuk("zvuk_maslo2.mp3"), nacti_zvuk("zvuk_maslo3.mp3")]
}

try: 
    pygame.mixer.music.load("hudba_pozadi.mp3")
    pygame.mixer.music.set_volume(1.0) # Hudba na 100 %
except pygame.error: pass

# --- MIXOVÁNÍ HLASITOSTI ---
# Ztlumíme zvuky výstřelů na 30 %
for z in zvuky_vystrel:
    if z: z.set_volume(0.3)

# Ztlumíme zvuky objevení na 40 %
for seznam in zvuky_objeveni.values():
    for z in seznam:
        if z: z.set_volume(0.4)

# Zvuk bodu a konce necháme trochu hlasitější
if zvuk_bod: zvuk_bod.set_volume(0.5)
if zvuk_konec: zvuk_konec.set_volume(0.8)

def prehraj_vystrel():
    platne = [z for z in zvuky_vystrel if z is not None]
    if platne: random.choice(platne).play()

def prehraj_specificky(typ_cile):
    seznam_zvuku = zvuky_objeveni.get(typ_cile, [])
    platne = [z for z in seznam_zvuku if z is not None]
    if platne: random.choice(platne).play()

# --- HERNÍ PROMĚNNÉ ---
stav_hry = "MENU"
skore = 0
zbyvajici_cas = 60 # Hra na 1 minutu
casovac_udalost = pygame.USEREVENT + 1

# Proměnné pro animaci skóre na konci hry
zobrazene_skore = 0
pocitani_hotovo = False
cas_dalsiho_pipnuti = 0

seznam_hlasek = ["Voda je mokrá!", "Nebuď slabej!", "oho!", "Vrrr!", "Au!", "Hokej!", "Potassium!", "PEANUT!"]
letajici_hlasky = []

vsechny_typy = ["veverka", "krokodyl", "banan", "izp", "hokej", "maslo"]
ulovky = {typ: 0 for typ in vsechny_typy} 
cile = [] 

def vytvor_cil():
    typ = random.choice(vsechny_typy)
    x = random.randint(0, SIRKA - 100)
    y = random.randint(80, VYSKA - 100)
    prehraj_specificky(typ)
    return {"typ": typ, "rect": pygame.Rect(x, y, 100, 100), "stav": "ZIVA", "cas_smrti": 0, "cas_zrozeni": pygame.time.get_ticks()}

def ziskej_verdikt():
    if sum(ulovky.values()) == 0: return "Wow, buď jsi zapomněl jak hrát anebo si true pacifist nebo učitel"
    nejvice = max(ulovky, key=ulovky.get)
    if nejvice == "izp": return "No nandal jsi to IZPéčku, jsi opravdu true fan of IZP"
    elif nejvice == "maslo": return "PEANUT! Buď nejíš maso anebo máš brutální alergii jak Béďa. Víš co je dobré."
    elif nejvice == "hokej": return "Gól! Buď chceš střílet jako Pastrňák anebo jsi průměrný český fanoušek hokeje."
    elif nejvice == "banan": return "Banán, tvoje guilty pleasure... Jsi buď velký gurmán exotiky anebo ezo maniak."
    elif nejvice == "krokodyl": return "Krokodýl, tvůj největší broski. Jsi buď lovcem anebo zaměstnancem ZOO u Vinotéky u hada."
    elif nejvice == "veverka": return "Zase samé veverky. Jsi buď žhář Českého Švýcarska anebo prostě rád týráš zvířata"
    else: return "Střílíš úplně po všem!"

# --- HLAVNÍ SMYČKA ---
running = True
while running:
    screen.fill((30, 39, 46))
    mys_x, mys_y = pygame.mouse.get_pos()
    aktualni_cas = pygame.time.get_ticks()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if stav_hry == "MENU":
                stav_hry = "HRA"
                skore = 0
                zbyvajici_cas = 60
                ulovky = {typ: 0 for typ in vsechny_typy}
                letajici_hlasky.clear()
                
                cile = []
                for i in range(4):
                    cil = vytvor_cil()
                    cil["cas_zrozeni"] += (i * 250)
                    cile.append(cil)
                    
                pygame.time.set_timer(casovac_udalost, 1000)
                try: pygame.mixer.music.play(-1)
                except pygame.error: pass
            
            elif stav_hry == "HRA":
                for cil in reversed(cile): 
                    if cil["stav"] == "ZIVA" and cil["rect"].collidepoint(event.pos):
                        prehraj_vystrel()
                        
                        cil["stav"] = "MRTVA"
                        cil["cas_smrti"] = aktualni_cas
                        ulovky[cil["typ"]] += 1
                        skore += 1
                        
                        letajici_hlasky.append({
                            "text": random.choice(seznam_hlasek),
                            "x": event.pos[0] - 20, "y": event.pos[1] - 20,
                            "zivot": 45
                        })
                        break

            elif stav_hry == "KONEC" and pocitani_hotovo:
                stav_hry = "MENU"

        if event.type == casovac_udalost and stav_hry == "HRA":
            zbyvajici_cas -= 1
            if zbyvajici_cas <= 0:
                stav_hry = "KONEC"
                pygame.time.set_timer(casovac_udalost, 0)
                pygame.mixer.music.stop()
                
                zobrazene_skore = 0
                pocitani_hotovo = False
                cas_dalsiho_pipnuti = aktualni_cas

    # --- LOGIKA BĚHEM HRY ---
    if stav_hry == "HRA":
        for i, cil in enumerate(cile):
            if cil["stav"] == "MRTVA" and aktualni_cas - cil["cas_smrti"] > 400:
                cile[i] = vytvor_cil()
            elif cil["stav"] == "ZIVA" and aktualni_cas - cil["cas_zrozeni"] > 1000:
                cile[i] = vytvor_cil()

    # --- LOGIKA NAČÍTÁNÍ SKÓRE NA KONCI ---
    if stav_hry == "KONEC" and not pocitani_hotovo:
        if aktualni_cas >= cas_dalsiho_pipnuti:
            if zobrazene_skore < skore:
                zobrazene_skore += 1
                if zvuk_bod:
                    zvuk_bod.stop()
                    zvuk_bod.play()
                cas_dalsiho_pipnuti = aktualni_cas + 60
            else:
                pocitani_hotovo = True
                if zvuk_konec: zvuk_konec.play()

    # --- VYKRESLOVÁNÍ ---
    if stav_hry == "MENU":
        nadpis = velky_font.render("Trénink reflexů: Hard Edition", True, (255, 255, 255))
        podtitul = font.render("Klikni pro START", True, (11, 232, 129))
        screen.blit(nadpis, (SIRKA//2 - nadpis.get_width()//2, VYSKA//3))
        screen.blit(podtitul, (SIRKA//2 - podtitul.get_width()//2, VYSKA//2))
        
    elif stav_hry == "HRA":
        # Skóre jsme záměrně skryli, zobrazujeme pouze zbývající čas
        screen.blit(font.render(f"Čas: {zbyvajici_cas} s", True, (255, 255, 255)), (SIRKA - 150, 20))
        
        for cil in cile:
            if cil["stav"] == "ZIVA": screen.blit(obrazky_zive[cil["typ"]], cil["rect"])
            else: screen.blit(obrazky_mrtve[cil["typ"]], cil["rect"])
                
        for hlaska in letajici_hlasky[:]:
            text_surface = mensi_font.render(hlaska["text"], True, (255, 215, 0))
            screen.blit(text_surface, (hlaska["x"], hlaska["y"]))
            hlaska["y"] -= 3
            hlaska["zivot"] -= 1
            if hlaska["zivot"] <= 0: letajici_hlasky.remove(hlaska)
        
    elif stav_hry == "KONEC":
        nadpis = velky_font.render("KONEC HRY!", True, (255, 255, 255))
        screen.blit(nadpis, (SIRKA//2 - nadpis.get_width()//2, VYSKA//6))
        
        skore_text = velky_font.render(f"Celkové skóre: {zobrazene_skore}", True, (255, 215, 0))
        screen.blit(skore_text, (SIRKA//2 - skore_text.get_width()//2, VYSKA//3 - 10))
        
        if pocitani_hotovo:
            r1 = f"Veverky: {ulovky['veverka']} | Krokodýli: {ulovky['krokodyl']} | Banány: {ulovky['banan']}"
            r2 = f"IZP: {ulovky['izp']} | Hokej: {ulovky['hokej']} | Máslo: {ulovky['maslo']}"
            stats1 = mensi_font.render(r1, True, (200, 200, 200))
            stats2 = mensi_font.render(r2, True, (200, 200, 200))
            
            verdikt_nadpis = font.render("Tvůj psychologický profil:", True, (11, 232, 129))
            verdikt_text = font.render(ziskej_verdikt(), True, (255, 255, 255))
            
            screen.blit(stats1, (SIRKA//2 - stats1.get_width()//2, VYSKA//2))
            screen.blit(stats2, (SIRKA//2 - stats2.get_width()//2, VYSKA//2 + 35))
            screen.blit(verdikt_nadpis, (SIRKA//2 - verdikt_nadpis.get_width()//2, VYSKA//2 + 90))
            screen.blit(verdikt_text, (SIRKA//2 - verdikt_text.get_width()//2, VYSKA//2 + 130))

    stred_kurzoru_x = mys_x - kurzor_img.get_width() // 2
    stred_kurzoru_y = mys_y - kurzor_img.get_height() // 2
    screen.blit(kurzor_img, (stred_kurzoru_x, stred_kurzoru_y))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()