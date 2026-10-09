"""Ilustraciones vectoriales originales para los símbolos específicos de la PoC.

No sustituyen una validación de comprensión con usuarios CAA. No se trazaron
ni modificaron imágenes ARASAAC. Se conservan las etiquetas del catálogo.
"""
from html import escape


def path(d, fill="none", extra=""):
    return f'<path d="{d}" fill="{fill}" {extra}/>'


def ellipse(x, y, rx, ry, color):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{color}"/>'


def circle(x, y, r, color):
    return ellipse(x, y, r, r, color)


def eye(x, y):
    return circle(x, y, 3.5, "#182d34")


def tree(x, y, scale=1, tropical=False):
    color = "#38a66a" if tropical else "#5b9851"
    return f'<g transform="translate({x} {y}) scale({scale})">'+path("M-5 0V-55H5V0Z", "#99633a")+circle(-18,-59,24,color)+circle(18,-59,24,color)+circle(0,-80,27,color)+"</g>"


def sun(x=160, y=45):
    return circle(x,y,17,"#f9c64e")+"".join(path(f"M{x+dx} {y+dy}l{dx//2} {dy//2}") for dx,dy in [(0,-25),(25,0),(0,25),(-25,0),(18,18),(-18,-18),(18,-18),(-18,18)])


def waves(y=125, color="#79c5ed"):
    return path(f"M18 {y}Q36 {y-16} 54 {y}T90 {y}T126 {y}T162 {y}T198 {y}V185H18Z",color)+path(f"M22 {y+22}Q38 {y+10} 54 {y+22}T86 {y+22}T118 {y+22}T150 {y+22}T182 {y+22}")


def mountain():
    return path("M15 180L84 42L139 153L161 88L207 180Z","#8aabb8")+path("M62 86L84 42L106 86L83 72Z","#fff")+path("M146 118L161 88L178 121L162 110Z","#fff")


def thermo(hot=True):
    return path("M85 143V40Q85 19 105 19T125 40V143A34 34 0 1 1 85 143Z","#fff")+circle(105,162,21,"#ee6f51" if hot else "#64b7d5")+path("M105 150V48" if hot else "M105 150V98", extra='stroke="#ee6f51" stroke-width="13"')+path("M137 55h13M137 82h13M137 109h13")


def fox(color, big=False):
    return path("M118 134Q170 95 198 127Q202 168 156 170L118 157Z",color)+path("M181 116Q204 130 189 153L174 143Z","#fff")+ellipse(99,136,50,32,color)+path("M60 148L59 181H79L85 151M116 151L121 181H141L136 147",color)+path("M62 101L42 42L79 76L106 35L119 106Z" if big else "M61 106L56 61L83 82L112 61L116 107Z",color)+path("M54 97L123 97L96 138L73 137Z",color)+path("M64 112L90 126L113 108L96 139L73 138Z","#fff")+eye(73,106)+eye(103,103)+circle(90,129,5,"#182d34")


def spotted_cat(color):
    s=path("M150 136Q203 152 194 93",extra='stroke-width="11"')+ellipse(109,127,54,31,color)+path("M61 139L54 177H74L86 142M131 142L134 177H157L153 137",color)+circle(61,97,30,color)+path("M36 77L33 54L53 69M68 71L86 56L85 88",color)+ellipse(55,110,18,12,"#fff")+eye(48,92)+eye(70,92)+circle(57,106,5,"#182d34")
    for x,y in [(96,112),(124,111),(150,124),(100,138),(124,131),(60,78)]:
        s+=circle(x,y,6,color)+eye(x-3,y-3)+eye(x+3,y+3)
    return s


def turtle(marine=False):
    color="#669957"
    legs=path("M61 114L23 155L67 149M127 123L172 166L151 130M73 81L37 66L60 111M142 83L177 64L156 109",color) if marine else path("M69 137L58 161L80 162L91 138M126 136L127 162H148L140 126M63 101L42 122L66 129",color)
    return legs+ellipse(111,113,59,40,"#a1b666")+path("M81 90L111 76L138 91L138 121L111 145L81 127Z","#74914d")+path("M81 90L57 102M81 127L67 140M138 91L156 98M138 121L166 133M111 76V96L138 106M111 96L81 109M111 96V127L138 121M111 127L81 127")+ellipse(172,105,22,16,color)+eye(181,100)


def dolphin(pink=False):
    color="#eaa8b5" if pink else "#789dbb"
    return path("M30 127Q64 67 127 91L153 56L146 102Q169 114 193 110L177 126Q188 135 204 126Q183 157 158 137Q103 164 55 142L33 170L35 138L15 150Z",color)+path("M82 130L100 164L114 140",color)+eye(169,115)


def original_animal(a):
    if a in {"A01","A45"}:return spotted_cat("#e4ad4e" if a=="A01" else "#d9e0e3")
    if a in {"A14","A38"}:return fox("#efd499" if a=="A14" else "#f1f3f4",a=="A14")
    if a in {"A16","A24"}:return turtle(a=="A24")
    if a=="A33":return dolphin(True)
    if a=="A04":
        return path("M20 50H190",extra='stroke="#865935" stroke-width="14"')+path("M64 120Q32 118 39 59M135 113Q156 122 169 55",extra='stroke="#ad9273" stroke-width="23"')+ellipse(104,132,55,37,"#ad9273")+circle(65,132,29,"#ad9273")+ellipse(61,136,21,20,"#f1e5cc")+path("M44 126L59 140L72 124",extra='stroke="#675748" stroke-width="8"')+eye(52,130)+eye(69,131)+path("M45 62L43 45M36 62L33 46M164 59L167 43M172 57L177 42",extra='stroke-width="4"')
    if a=="A05":
        return path("M77 130L109 195L130 129Z","#2789c7")+ellipse(107,107,39,58,"#e95542")+path("M92 75Q62 106 82 142L110 116Z","#f4c84e")+path("M82 113L81 144L111 119Z","#2789c7")+circle(129,59,26,"#e95542")+ellipse(140,63,18,15,"#fff")+path("M150 60Q181 54 168 89L149 76Z","#393a3b")+eye(139,56)+path("M97 160V178M113 157V177M83 177H126")
    if a=="A06":
        s=path("M67 128L24 163L61 176L81 145M133 127L185 161L144 178L121 146M62 98L24 80L27 53M138 98L175 77L181 53","#2683d3")+ellipse(99,115,43,47,"#2683d3")+circle(73,76,15,"#2683d3")+circle(126,76,15,"#2683d3")+eye(73,73)+eye(126,73)
        return s+"".join(circle(x,y,5,"#182d34") for x,y in [(80,107),(115,102),(98,127),(76,138),(119,135)])
    if a=="A15":return path("M95 151Q48 192 32 175",extra='stroke="#bc9968" stroke-width="10"')+ellipse(111,131,29,56,"#c4a36e")+path("M96 98L74 133M124 100L146 123",extra='stroke="#c4a36e" stroke-width="12"')+circle(94,66,11,"#c4a36e")+circle(130,66,11,"#c4a36e")+ellipse(112,80,24,30,"#c4a36e")+ellipse(101,76,8,7,"#53493d")+ellipse(124,76,8,7,"#53493d")+ellipse(112,95,14,9,"#ede0bd")+eye(112,91)+path("M91 180H106M117 180H133")
    if a=="A17":
        s=path("M145 123Q207 130 194 169Q161 175 155 149", "#f49e68")+path("M72 109L41 80L30 91M120 106L154 80L163 90M76 131L51 161L39 153M125 137L150 167L169 155",extra='stroke="#343438" stroke-width="15"')+ellipse(104,124,61,26,"#313137")+ellipse(41,119,23,18,"#313137")+eye(31,113)
        return s+"".join(circle(x,y,6,"#f49e68") for x,y in [(60,111),(77,120),(89,134),(104,110),(126,121),(143,135),(39,128),(185,144),(175,165)])
    if a in {"A18","A48"}:
        c="#c6ad8a" if a=="A18" else "#a4acb8"
        return path("M120 136Q205 117 188 174Q164 194 149 172",extra=f'stroke="{c}" stroke-width="{5 if a=="A18" else 16}"')+ellipse(106,127,40,40,c)+ellipse(73,65,14,29,c)+ellipse(104,66,16,29,c)+circle(86,93,32,c)+ellipse(64,102,14,9,"#eee8df")+eye(66,88)+eye(56,101)+path("M99 130L137 157L91 181H65M104 109L79 125",extra=f'stroke="{c}" stroke-width="16"')+path("M53 108L33 102M56 114L32 116")
    if a=="A22":return path("M112 78Q75 72 19 124L77 148Q111 173 145 146L199 118Q151 72 112 78Z","#5e7283")+path("M99 81Q93 50 83 63L91 96M125 79Q134 50 144 62L134 93","#5e7283")+path("M112 150Q115 184 145 199",extra='stroke-width="7"')+eye(88,100)+eye(137,98)
    if a=="A32":
        g=path("M60 77L35 56M57 88L27 84M64 100L35 115M109 76L135 55M117 87L147 84M111 100L139 116",extra='stroke="#df6688" stroke-width="11"')
        return g+path("M133 131Q181 88 202 120Q193 156 143 157Z","#e8a4ba")+ellipse(114,136,48,26,"#e8a4ba")+path("M86 141L59 165M122 143L143 167M103 118L128 100",extra='stroke="#e8a4ba" stroke-width="12"')+ellipse(87,89,34,27,"#efbdcd")+eye(72,87)+eye(101,87)+path("M76 100Q88 108 99 99")
    if a=="A41":return path("M62 157Q49 118 61 92L70 60L91 69L111 65L136 62L148 96Q166 139 147 166Z","#f0f2f2")+ellipse(84,100,19,21,"#fff")+ellipse(125,100,19,21,"#fff")+circle(84,100,9,"#f7c851")+circle(125,100,9,"#f7c851")+eye(84,100)+eye(125,100)+path("M97 120L110 118L104 132Z","#d4a438")+path("M69 138L80 141M130 138L140 134M78 155L91 157M116 156L130 152M91 164V177M116 164V177M81 177H99M107 177H126")
    if a=="A42":return ellipse(109,130,48,34,"#f1f3f3")+circle(159,127,13,"#fff")+ellipse(65,104,30,26,"#f1f3f3")+ellipse(62,61,10,32,"#f1f3f3")+ellipse(85,65,11,32,"#f1f3f3")+path("M60 43V68M84 47V72",extra='stroke="#d0b8bf" stroke-width="5"')+ellipse(126,149,27,22,"#f1f3f3")+path("M72 124L58 162H84M111 164H143")+eye(54,96)+eye(38,107)
    if a=="A44":return path("M41 99Q77 71 142 93L168 95L181 136L163 151L148 129L142 168L130 161L112 174L102 165L83 175L72 162L58 169L45 151Z","#493e37")+path("M52 138L51 181H70L74 153M118 146L117 181H139L141 144","#493e37")+circle(160,96,28,"#493e37")+path("M143 81Q122 67 130 41Q136 67 153 68M172 80Q192 65 184 42Q181 64 165 70","#d6d1b9")+ellipse(175,111,18,14,"#a79276")+eye(171,89)+path("M40 109Q17 93 23 145",extra='stroke="#493e37" stroke-width="10"')
    if a=="A47":return ellipse(108,123,49,31,"#f3f0e6")+path("M65 139L58 180H78L86 142M129 142L132 180H153L151 133","#f3f0e6")+path("M144 92L148 117L183 104L169 79Z","#f3f0e6")+path("M146 83Q126 48 159 42Q137 51 158 78M164 80Q182 42 197 53Q181 56 179 90","#b6aba0")+eye(174,93)+path("M157 107L166 127L175 107","#f3f0e6")+path("M63 111L45 96")
    raise ValueError(a)


def habitat(h):
    if h=="H01":return path("M15 175Q110 146 200 175V190H15Z","#a3cf88")+tree(48,168,.85,True)+tree(108,174,1.1,True)+tree(171,172,.85,True)+sun(174,38)
    if h=="H02":return sun()+path("M15 142Q115 121 201 140V188H15Z","#e4cf76")+path("M48 179l-9-22M48 179l9-25M163 180l-8-24M163 180l8-21")+tree(113,145,.7)
    if h=="H03":return sun()+path("M15 160Q51 115 91 146Q145 110 200 148V188H15Z","#efc881")+path("M153 154V107M153 134Q139 136 139 117M153 143Q168 146 168 124",extra='stroke="#5b9861" stroke-width="9"')
    if h=="H04":return waves(106)+sun(170,48)
    if h=="H05":return path("M15 175H200V188H15Z","#b5ce97")+tree(47,174,.85)+tree(107,177,1.1)+tree(169,174,.8)
    if h=="H06":return path("M15 162Q100 118 200 161V189H15Z","#b2d292")+path("M95 71Q162 100 108 126Q65 151 91 190H159Q119 150 149 129Q191 99 126 71Z","#79c5ed")+tree(46,142,.6)+path("M173 169l5-31M178 155l12-11")
    if h=="H07":return waves(147)+path("M17 143L57 101L86 144L118 90L157 144L184 115L204 147Z","#eff7fa")+circle(45,52,20,"#aad5e8")+path("M45 26V78M19 52H71M27 34L64 71M64 33L26 72",extra='stroke="#4788ae"')
    if h=="H08":return mountain()
    raise ValueError(h)


def apoyo(p):
    if p in {"P_MUCHOS_ARBOLES","P_BOSQUE"}:return tree(48,180,.8)+tree(110,180,1)+tree(174,180,.8)
    if p=="P_ARBOLES_SEPARADOS":return tree(40,175,.55)+tree(174,175,.55)+path("M20 180H200")
    if p=="P_LUGAR_ABIERTO":return path("M20 165H199M20 138Q109 112 199 138",extra='stroke="#73a356"')+path("M45 165l-6-14M179 165l7-16")
    if p in {"P_CALOR","P_CLIMA_TEMPLADO"}:return thermo(p=="P_CALOR")
    if p=="P_PAISAJE_FRIO":return habitat("H07")
    if p in {"P_MUCHA_AGUA","P_AGUA_DULCE","P_AGUA_SALADA"}:
        s=waves(112)
        if p=="P_AGUA_SALADA":s+=path("M77 28H115L128 68H65Z","#deded8")+path("M80 43h3M98 43h3M77 81l-3 6M92 80v7M108 79l3 6")
        if p=="P_AGUA_DULCE":s+=path("M73 25Q140 51 91 72Q50 90 80 113H124Q88 91 131 75Q175 51 108 25Z","#79c5ed")
        return s
    if p=="P_RIO":return habitat("H06")
    if p=="P_HUMEDAD":return tree(83,182,.9,True)+path("M156 62Q197 120 162 129Q125 129 156 62Z","#78c6ef")
    if p in {"P_PASTO_ABUNDANTE","P_POCAS_PLANTAS"}:
        return "".join(path(f"M{x} 178l-13-33M{x} 178v-49M{x} 178l16-35",extra='stroke="#57934c" stroke-width="5"') for x in ([35,73,113,155,190] if p=="P_PASTO_ABUNDANTE" else [49,173]))+path("M17 182H201")
    if p=="P_SECO":return path("M20 133Q98 104 200 133V185H20Z","#e4c18e")+path("M80 119L97 144L83 169L103 185M97 144L123 147L134 166M83 169L49 168")
    if p in {"P_PLANETA","P_POLOS"}:
        s=circle(110,110,76,"#8acbe5")+ellipse(110,110,34,76,"none")+path("M36 110H184M50 64H170M50 157H170")
        if p=="P_POLOS":s+=circle(110,35,12,"#f0b84b")+circle(110,186,12,"#f0b84b")+path("M110 11V25M110 198V211",extra='stroke="#d4772e"')
        else:s+=path("M78 63L99 54L111 82L98 101L118 119L100 151L72 128L79 100L62 84Z","#87b877")
        return s
    if p=="P_MONTANAS_ALTAS":return mountain()
    if p in {"P_BUSCAR","P_EXPLORAR"}:return circle(89,87,49,"#c6e6f2")+path("M124 124L182 182",extra='stroke-width="15"')+path("M59 78Q66 57 88 56",extra='stroke="#fff" stroke-width="8"')
    if p in {"P_QUE_LUGAR","P_PREGUNTAR","P_AYUDA"}:return circle(110,109,80,"#f6d777" if p=="P_AYUDA" else "#d5e9dd")+'<text x="110" y="157" text-anchor="middle" font-family="Arial" font-size="136" font-weight="bold" stroke="none" fill="#182d34">?</text>'
    if p=="P_VIVIR":return tree(157,173,.8)+ellipse(68,139,32,20,"#d5af78")+circle(41,121,17,"#d5af78")+path("M50 147V174M78 150V174M101 98h38M127 88l13 10-13 10")
    if p in {"P_OPCION","P_ELEGIR"}:return '<rect x="21" y="51" width="77" height="110" rx="10" fill="#d5e9dd"/><rect x="121" y="51" width="77" height="110" rx="10" fill="#d6e6f2"/>'+path("M45 112L59 126L86 88",extra='stroke="#166452" stroke-width="9"')
    if p in {"P_TOCAR","P_SENALAR"}:return circle(111,58,31,"#f3d16d")+path("M100 159V79Q100 63 115 70V117L142 100Q160 94 167 116L150 177H101L74 140Q66 126 80 123Z","#f1c8a1")
    if p=="P_CONFIRMAR":return circle(110,110,78,"#d8efdf")+path("M57 111L94 145L164 72",extra='stroke="#166452" stroke-width="15"')
    if p in {"P_REPETIR","P_PROBAR"}:return path("M55 154A67 67 0 1 1 172 118",extra='stroke="#166452" stroke-width="13"')+path("M159 99L170 128L194 111Z","#166452")
    if p=="P_PAUSAR":return '<rect x="58" y="40" width="33" height="140" rx="8" fill="#166452"/><rect x="130" y="40" width="33" height="140" rx="8" fill="#166452"/>'
    if p in {"P_REANUDAR","P_INICIAR"}:return path("M69 37L175 110L69 182Z","#166452")
    if p=="P_CONTINUAR":return path("M28 93H119V52L194 110L119 169V128H28Z","#166452")
    if p=="P_SALIR":return '<rect x="28" y="28" width="105" height="164" rx="8" fill="#e3d8bc"/>'+path("M82 95H159V69L198 110L159 151V124H82Z","#166452")
    if p=="P_FIN":return path("M52 195V29M52 32H178L153 63L177 95H54", "#d5e9dd")+path("M66 47H84V62H103V47H121V62H141V47H163M66 78H84V63H103V78H121V63H141V78H157")
    if p=="P_AGENTE":return '<rect x="47" y="60" width="125" height="107" rx="22" fill="#d2e4e7"/>'+path("M109 58V32M26 91H45M173 91H194")+circle(109,26,10,"#f0c55a")+circle(82,106,13,"#166452")+circle(137,106,13,"#166452")+path("M84 143H135")
    if p=="P_JUGADOR":return circle(110,60,34,"#edc19a")+path("M76 54Q79 26 113 28Q137 33 142 52", "#745440")+path("M56 185V137Q56 103 90 105H133Q165 103 165 137V185Z","#80b8a3")+eye(96,63)+eye(123,63)+path("M96 80Q108 88 120 80")
    raise ValueError(p)


def svg(pid, etiqueta):
    cuerpo = original_animal(pid[2:]) if pid.startswith("P_A") and len(pid)==5 else habitat(pid[2:]) if pid.startswith("P_H") and len(pid)==5 else apoyo(pid)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 220" width="500" height="500"><title>{escape(etiqueta)}</title><rect width="220" height="220" fill="white"/><g stroke="#263b42" stroke-width="3.8" stroke-linejoin="round" stroke-linecap="round">{cuerpo}</g></svg>'
