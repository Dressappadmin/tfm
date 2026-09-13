CATEGORIAS_COMPLETAS = [
    'family',
    'abrigo',
    'braga/calzoncillo',
    'short',
    'pañoletas/foulard',
    'camisa',
    'maquill.labios',
    'sujetador',
    'eau de toilette',
    'bolsos',
    'maquillaje facial',
    'sandalia tacon',
    'bota tacon',
    'cinturones',
    'monedero billetera',
    'gorro',
    'body',
    'botin plano',
    'paraguas',
    'zapato tacon',
    'bisuteria',
    'tops y otras p.',
    'maquillaje ojos',
    'complementos',
    'accesorios',
    'cazadora',
    'baño',
    'guante',
    'bota plana',
    'blazer',
    'perfume',
    'cosmetica pelo',
    'running',
    'mono',
    'gabardina impermea',
    'anorak',
    'calzado deportivo',
    'zapato plano',
    'chaqueta',
    'locion corporal',
    'sudadera',
    'leggings',
    'vestido',
    'peto',
    'falda',
    'ocio y deporte',
    'calcetin',
    'sandalia plana',
    'bambas',
    'contorno ojos',
    'bermuda',
    'eau de perfume',
    'jersey',
    'chaleco',
    'pantalon',
    'botin tacon',
    'camiseta'
]

CATEGORIAS = [
    'family',
    'abrigo',
    'braga/calzoncillo',
    'short',
    'pañoletas/foulard',
    'camisa',
    'sujetador',
    'bolsos',
    'sandalia tacon',
    'bota tacon',
    'cinturones',
    'monedero billetera',
    'gorro',
    'body',
    'botin plano',
    'paraguas',
    'zapato tacon',
    'bisuteria',
    'tops y otras p.',
    'complementos',
    'accesorios',
    'cazadora',
    'baño',
    'guante',
    'bota plana',
    'blazer',
    'mono',
    'gabardina impermea',
    'anorak',
    'calzado deportivo',
    'zapato plano',
    'chaqueta',
    'sudadera',
    'leggings',
    'vestido',
    'peto',
    'falda',
    'calcetin',
    'sandalia plana',
    'bambas',
    'bermuda',
    'jersey',
    'chaleco',
    'pantalon',
    'botin tacon',
    'camiseta'
]

SLOTS_COMPLETOS = { 
    'SUPERIOR':        ['camiseta', 'camisa', 'tops y otras p.', 'jersey', 'sudadera', 'body', 'chaleco'],
    'INFERIOR':        ['pantalon', 'falda', 'short', 'bermuda', 'leggings'],
    'CUERPO_COMPLETO': ['vestido', 'mono', 'peto', 'baño'],
    'ABRIGO':          ['abrigo', 'anorak', 'chaqueta', 'cazadora', 'gabardina impermea', 'blazer'],
    'CALZADO':         ['bambas', 'bota plana', 'bota tacon', 'botin plano', 'botin tacon', 'zapato tacon', 'zapato plano', 'sandalia tacon', 'sandalia plana', 'calzado deportivo'],
    'ACCESORIO':       ['bisuteria', 'bolsos', 'cinturones', 'pañoletas/foulard', 'gorro', 'paraguas', 'monedero billetera', 'complementos', 'accesorios', 'guante'],
    'ROPA INTERIOR':   ['braga/calzoncillo', 'sujetador', 'calcetin'],
    'MAQUILLAJE':      ['maquill.labios', 'maquillaje facial', 'maquillaje ojos', 'contorno ojos'],
    'PERFUMERÍA':      ['eau de toilette', 'eau de perfume', 'perfume', 'locion corporal', 'cosmetica pelo'],
    'DEPORTE':         ['running', 'ocio y deporte']
}

SLOTS = { 
    'SUPERIOR':        ['camiseta', 'camisa', 'tops y otras p.', 'jersey', 'sudadera', 'body', 'chaleco'],
    'INFERIOR':        ['pantalon', 'falda', 'short', 'bermuda', 'leggings'],
    'CUERPO_COMPLETO': ['vestido', 'mono', 'peto'],
    'ABRIGO':          ['abrigo', 'anorak', 'chaqueta', 'cazadora', 'gabardina impermea', 'blazer'],
    'CALZADO':         ['bambas', 'bota plana', 'bota tacon', 'botin plano', 'botin tacon', 'zapato tacon', 'zapato plano', 'sandalia tacon', 'sandalia plana', 'calzado deportivo']
}

MAPA_PRENDAS = {prenda: slot for slot, prendas in SLOTS.items() for prenda in prendas}

TODOS_LOS_SLOTS = list(SLOTS.keys())

SLOT_INDEX = {slot: indice for indice, slot in enumerate(TODOS_LOS_SLOTS)}

TOP_K = 5

VOCABULARIO_TAGS = [
    # Ocasión
    "Casual", "Formal-Oficina", "Fiesta-Discoteca", "Fiesta-Elegante", "Deporte", "Otros" ,
    # Temporalidad
    "Invierno", "Verano", "Entretiempo",
]

NUM_TAGS = len(VOCABULARIO_TAGS)