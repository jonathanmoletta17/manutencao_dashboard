# Padrões Visuais do Dashboard de Manutenção
## Documentação Completa para Replicação no Dashboard de Carregadores

---

## 🎨 **PALETA DE CORES PRINCIPAL**

### Cor Primária (Azul Institucional)
- **Cor Principal**: `#5A9BD4` (oklch(.546 .245 262.881))
- **Variação Hover**: `#4A8BC2`
- **Uso**: Header, ícones principais, badges, scrollbars, bordas de destaque

### Cores de Status (Sistema de Estados)
- **Novos**: `#5A9BD4` (azul primário)
- **Em Atendimento**: `#1E3A8A` (azul escuro - oklch(.379 .146 265.522))
- **Pendentes**: `#D97706` (âmbar - oklch(.666 .179 58.318))
- **Planejados**: `#EA580C` (laranja - oklch(.646 .222 41.116))
- **Resolvidos**: `#16A34A` (verde - oklch(.627 .194 149.214))

### Cores de Fundo e Neutras
- **Fundo Principal**: `#F3F4F6` (gray-100)
- **Cards/Componentes**: `#FFFFFF` (branco)
- **Fundo Alternativo**: `#F9FAFB` (gray-50)
- **Bordas**: `#E5E7EB` (gray-200)
- **Texto Principal**: `#111827` (gray-900)
- **Texto Secundário**: `#6B7280` (gray-500)
- **Texto Terciário**: `#9CA3AF` (gray-400)

### Cores de Ranking (Pódio)
- **1º Lugar**: Gradiente `from-[#5A9BD4] to-[#4A8BC2]` + Badge `#EAB308` (yellow-500)
- **2º Lugar**: Gradiente `from-slate-600 to-slate-700` + Badge `#D1D5DB` (gray-300)
- **3º Lugar**: Gradiente `from-orange-600 to-orange-700` + Badge `#FED7AA` (orange-200)

---

## 📝 **TIPOGRAFIA**

### Hierarquia de Fontes
- **Font Family**: `ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"`
- **Font Mono**: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace`

### Tamanhos de Texto
- **text-xs**: `0.75rem` (12px) - Labels, badges, informações secundárias
- **text-sm**: `0.875rem` (14px) - Texto padrão de componentes
- **text-base**: `1rem` (16px) - Texto principal
- **text-lg**: `1.125rem` (18px) - Títulos de seções
- **text-xl**: `1.25rem` (20px) - Números de métricas
- **text-2xl**: `1.5rem` (24px) - Títulos principais

### Pesos de Fonte
- **font-normal**: `400` - Texto padrão
- **font-medium**: `500` - Texto de destaque
- **font-semibold**: `600` - Títulos e labels importantes
- **font-bold**: `700` - Números de ranking

---

## 📐 **ESPAÇAMENTO E LAYOUT**

### Sistema de Espaçamento (baseado em 0.25rem)
- **gap-1**: `0.25rem` (4px)
- **gap-2**: `0.5rem` (8px)
- **gap-3**: `0.75rem` (12px)
- **gap-4**: `1rem` (16px)
- **gap-6**: `1.5rem` (24px)

### Padding Padrão
- **Cards**: `p-3` (12px) para conteúdo, `px-6 pt-6` para headers
- **Componentes pequenos**: `p-2` ou `p-3`
- **Header**: `p-3 px-6`

### Margens e Espaçamentos
- **Entre seções**: `gap-4` (16px)
- **Entre elementos**: `gap-2` ou `gap-3`
- **Espaçamento interno**: `space-y-3` para listas

---

## 🧩 **COMPONENTES DE INTERFACE**

### Cards (Padrão Principal)
```css
.card-base {
  background: #FFFFFF;
  border-radius: 0.75rem; /* rounded-xl */
  box-shadow: 0 1px 3px rgba(0,0,0,0.1); /* shadow-sm */
  border: 1px solid transparent;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
```

### Cards de Métricas (Stats)
- **Estrutura**: Borda colorida à esquerda (4px), ícone circular, número grande
- **Borda esquerda**: `border-l-4` com cor específica do status
- **Ícone**: Círculo de 40x40px com fundo colorido (10% opacity)
- **Layout**: Flexbox com justify-between

### Badges
```css
.badge-primary {
  background: #5A9BD4;
  color: white;
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  border-radius: 0.375rem;
  font-weight: 500;
}
```

### Botões
- **Ghost**: Fundo transparente, hover com `bg-accent`
- **Primary**: Fundo `#5A9BD4`, texto branco
- **Tamanhos**: `sm` (32px), `default` (36px), `lg` (40px)

---

## 🎯 **LAYOUT E ESTRUTURA**

### Header
- **Altura**: Fixa, aproximadamente 64px
- **Fundo**: `#5A9BD4` (azul primário)
- **Conteúdo**: Logo + título à esquerda, controles à direita
- **Elementos**: DateRangePicker, botão refresh, avatar do usuário

### Grid Principal
```css
.dashboard-layout {
  min-height: 100vh;
  background: #F3F4F6;
  display: flex;
  flex-direction: column;
}

.content-area {
  padding: 1.5rem;
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  overflow: hidden;
}
```

### Distribuição de Colunas
1. **Stats Row**: Grid de 5 colunas (métricas principais)
2. **Main Content**: 
   - Esquerda: Grid 2x1 (Rankings de Entidades e Categorias)
   - Direita: Sidebar fixa (Tickets Novos) - largura `w-130`
3. **Bottom**: Ranking de Técnicos (largura total)

---

## 🔄 **COMPONENTES INTERATIVOS**

### Scrollbars Customizadas
```css
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #5A9BD4 #f1f5f9;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #5A9BD4;
  border-radius: 2px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #4A8BC2;
}
```

### Carrossel de Categorias
- **Indicadores**: Círculos pequenos (5x5px)
- **Ativo**: `#5A9BD4` com 65% opacity
- **Inativo**: Transparente com borda `rgba(0,0,0,0.22)`
- **Controles**: Chevrons com hover `bg-gray-100`

### DateRangePicker
- **Container**: `bg-white/20` com `rounded-lg`
- **Inputs**: Fundo transparente, texto branco
- **Labels**: `text-white/80`

---

## 📊 **PADRÕES DE DADOS**

### Rankings e Listas
- **Item de Ranking**: 
  - Fundo `bg-gray-50`
  - Borda `border-gray-200`
  - Padding `p-3`
  - Border radius `rounded-lg`
  - Número do ranking em `text-xs font-bold text-gray-600`

### Tickets Novos
- **Container**: Borda esquerda azul `border-l-4 border-[#5A9BD4]`
- **Fundo**: `bg-[#5A9BD4]/5` (5% opacity)
- **ID**: Badge mono `font-mono` com fundo `bg-gray-100`
- **Status**: Badge outline azul

### Ranking de Técnicos (Horizontal)
- **Dimensões**: Cards de 143x117px
- **Top 3**: Gradientes específicos com badges coloridas
- **Demais**: Fundo `bg-gray-50` com borda

---

## 🎨 **ESTADOS E FEEDBACK**

### Estados de Loading
- **Texto**: `"Carregando…"` em `text-gray-600 text-xs`
- **Centralizado**: `text-center py-2`

### Estados Vazios
- **Texto**: `"Ranking indisponível"` ou similar
- **Estilo**: Mesmo do loading

### Estados de Erro
- **Container**: `bg-red-50 border-l-4 border-red-500`
- **Texto**: `text-red-700 text-sm`
- **Estrutura**: Título em `font-medium` + detalhes em `opacity-80`

---

## 🔧 **UTILITÁRIOS E HELPERS**

### Truncamento de Texto
- **Classes**: `truncate` para overflow
- **Tooltip**: Atributo `title` com texto completo

### Responsividade
- **Breakpoints**: Uso de classes `md:` para ajustes
- **Gaps**: Ajuste de `gap-3` para `md:gap-4`

### Transições
- **Padrão**: `transition-all` com duração `0.15s`
- **Timing**: `cubic-bezier(0.4, 0, 0.2, 1)`

---

## 📋 **CHECKLIST PARA REPLICAÇÃO**

### ✅ Cores
- [ ] Implementar paleta de cores principal (#5A9BD4)
- [ ] Definir cores de status para cada estado
- [ ] Configurar cores de ranking (gradientes do pódio)
- [ ] Estabelecer cores neutras (fundos, bordas, textos)

### ✅ Tipografia
- [ ] Configurar font families (sans-serif + mono)
- [ ] Implementar hierarquia de tamanhos
- [ ] Definir pesos de fonte

### ✅ Layout
- [ ] Estrutura de header com altura fixa
- [ ] Grid principal com distribuição de colunas
- [ ] Sistema de espaçamento consistente

### ✅ Componentes
- [ ] Cards com padrão visual estabelecido
- [ ] Badges com variações de cor
- [ ] Botões com estados (ghost, primary)
- [ ] Scrollbars customizadas

### ✅ Interações
- [ ] Estados de hover consistentes
- [ ] Transições suaves
- [ ] Feedback visual para ações

---

**Nota**: Este documento serve como referência completa para manter a consistência visual entre todos os dashboards do sistema. Todos os valores, cores e padrões devem ser replicados exatamente no dashboard de carregadores para garantir uma experiência de usuário uniforme.