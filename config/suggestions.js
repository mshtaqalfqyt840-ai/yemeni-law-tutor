// ── الاقتراحات الافتراضية للواجهة الأمامية ──

const DEFAULT_SUGGESTIONS = [
  {
    id: "sug_0",
    category: "باب العقود والالتزامات",
    title: "أركان العقد وشروط صحته",
    subtext: "استعراض الأهلية، التراضي، ومحل العقد وفقاً لأحكام القانون المدني",
    prompt: "ما هي أركان العقد وشروط صحته وفقاً للقانون المدني اليمني؟",
    btn_label: "استعراض الأركان والشروط ⚡",
    svg_icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
    accent_class: "sug-accent-gold",
  },
  {
    id: "sug_1",
    category: "تأصيل قانوني مباشر",
    title: "المادة (138) بالتفصيل",
    subtext: "النص الحرفي والشرح التطبيقي لأحكام المادة مع الأمثلة",
    prompt: "138",
    btn_label: "قراءة نص المادة (138) 📜",
    svg_icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-0.5-.05"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15Z"/><path d="M6 12h8"/><path d="M6 16h8"/><path d="M6 8h4"/></svg>`,
    accent_class: "sug-accent-emerald",
  },
  {
    id: "sug_2",
    category: "النظرية العامة للحق",
    title: "عيوب الإرادة وأثرها القانوني",
    subtext: "الغلط، التدليس، الإكراه، والاستغلال وفقاً لأحكام القانون المدني",
    prompt: "ما هي عيوب الإرادة في القانون المدني اليمني وكيف أثرها؟",
    btn_label: "تحليل عيوب الإرادة ⚖️",
    svg_icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h18"/></svg>`,
    accent_class: "sug-accent-blue",
  },
  {
    id: "sug_3",
    category: "الضمانات وحقوق الدائن",
    title: "أحكام الكفالة والضمان",
    subtext: "التزامات الكفيل وحقوق الدائن والمدين في الشريعة والقانون",
    prompt: "ما هي أحكام الكفالة والضمان ومسؤولية الكفيل في القانون اليمني؟",
    btn_label: "استعراض أحكام الكفالة 🛡️",
    svg_icon: `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>`,
    accent_class: "sug-accent-purple",
  },
];

module.exports = { DEFAULT_SUGGESTIONS };
