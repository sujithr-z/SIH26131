// =====================================================================
// CropGuard Multilingual Dictionary: English, Hindi, Tamil, Malayalam
// =====================================================================

const TRANSLATIONS = {
  en: {
    greeting_small: "Good morning,",
    diagnose_headline: "Diagnose Crop",
    diagnose_subtext: "Upload a clear close-up photo of the affected plant leaf or stem to detect diseases in seconds.",
    dropzone_title: "Take or Upload Photo",
    dropzone_sub: "Tap to open camera or drag & drop leaf picture here",
    warn_lighting: "Make sure lighting is bright",
    btn_analyze: "⚙️ Analyze Crop Health",
    btn_voice: "🎙️ Voice Input (Speak Crop Issue)",
    btn_gps: "📍 Fetch Current GPS",
    field_label: "Select Field:",
    crop_label: "Crop Type:",
    followup_label: "This is a follow-up recovery photo for a past case",
    history_link: "📋 View My Past Observations",
    logout: "Log out",
    active_alert_title: "LOCAL SURVEILLANCE WARNING",
    active_alert_sub: "Confirmed disease risk in your area. Tap for action steps.",
    speak_prompt: "Listening... Please describe the visible leaf symptoms or crop issue.",
  },
  hi: {
    greeting_small: "नमस्ते,",
    diagnose_headline: "फसल रोग निदान",
    diagnose_subtext: "रोगों का तुरंत पता लगाने के लिए प्रभावित पौधे की पत्ती या तने की स्पष्ट फोटो अपलोड करें।",
    dropzone_title: "फोटो लें या अपलोड करें",
    dropzone_sub: "कैमरा खोलने के लिए टैप करें या पत्ती की तस्वीर यहां छोड़ें",
    warn_lighting: "सुनिश्चित करें कि प्रकाश पर्याप्त है",
    btn_analyze: "⚙️ फसल स्वास्थ्य की जांच करें",
    btn_voice: "🎙️ आवाज से बोलें (Voice Input)",
    btn_gps: "📍 वर्तमान GPS स्थान प्राप्त करें",
    field_label: "खेत चुनें:",
    crop_label: "फसल का प्रकार:",
    followup_label: "यह पिछले मामले की फॉलो-अप रिकवरी फोटो है",
    history_link: "📋 मेरी पिछली जांच और इतिहास देखें",
    logout: "लॉग आउट करें",
    active_alert_title: "स्थानीय रोग निगरानी चेतावनी",
    active_alert_sub: "आपके क्षेत्र में रोग का खतरा पाया गया है। समाधान के लिए टैप करें।",
    speak_prompt: "सुन रहे हैं... कृपया फसल की समस्या या पत्ती के लक्षण बताएं।",
  },
  ta: {
    greeting_small: "வணக்கம்,",
    diagnose_headline: "பயிர் நோய் கண்டறிதல்",
    diagnose_subtext: "நோய்களை நொடிகளில் கண்டறிய பாதிக்கப்பட்ட இலை அல்லது தண்டின் தெளிவான புகைப்படத்தை பதிவேற்றவும்.",
    dropzone_title: "புகைப்படம் எடுக்கவும் அல்லது பதிவேற்றவும்",
    dropzone_sub: "கேமராவைத் திறக்க தட்டவும் அல்லது புகைப்படத்தை இங்கே விடவும்",
    warn_lighting: "வெளிச்சம் போதுமானதாக இருப்பதை உறுதிசெய்யவும்",
    btn_analyze: "⚙️ பயிர் ஆரோக்கியத்தை பகுப்பாய்வு செய்",
    btn_voice: "🎙️ குரல் உள்ளீடு (Voice Input)",
    btn_gps: "📍 தற்போதைய GPS இருப்பிடத்தைப் பெறவும்",
    field_label: "நிலத்தைத் தேர்ந்தெடுக்கவும்:",
    crop_label: "பயிர் வகை:",
    followup_label: "இது முந்தைய வழக்கிற்கான பின்தொடர்தல் மீட்பு புகைப்படம்",
    history_link: "📋 எனது முந்தைய பதிவுகள் மற்றும் வரலாறு",
    logout: "வெளியேறு",
    active_alert_title: "உள்ளூர் பயிர் நோய் எச்சரிக்கை",
    active_alert_sub: "உங்கள் பகுதியில் நோய் அபாயம் உறுதி செய்யப்பட்டுள்ளது. வழிகாட்டுதலுக்கு தட்டவும்.",
    speak_prompt: "கேட்கிறது... பயிர் அறிகுறிகளைப் பேசுங்கள்.",
  },
  ml: {
    greeting_small: "നമസ്കാരം,",
    diagnose_headline: "വിള രോഗനിർണയം",
    diagnose_subtext: "സെക്കൻഡുകൾക്കുള്ളിൽ രോഗങ്ങൾ കണ്ടെത്താൻ ബാധിച്ച ഇലയുടെ വ്യക്തമായ ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക.",
    dropzone_title: "ഫോട്ടോ എടുക്കുക അല്ലെങ്കിൽ അപ്‌ലോഡ് ചെയ്യുക",
    dropzone_sub: "ക്യാമറ തുറക്കാൻ ടാപ്പ് ചെയ്യുക അല്ലെങ്കിൽ ഫോട്ടോ ഇവിടെ വലിച്ചിടുക",
    warn_lighting: "നല്ല വെളിച്ചമുണ്ടെന്ന് ഉറപ്പാക്കുക",
    btn_analyze: "⚙️ വിളാരോഗ്യം പരിശോധിക്കുക",
    btn_voice: "🎙️ വോയ്സ് ഇൻപുട്ട് (സംസാരിക്കുക)",
    btn_gps: "📍 നിലവിലെ GPS ലൊക്കേഷൻ എടുക്കുക",
    field_label: "പാടം തിരഞ്ഞെടുക്കുക:",
    crop_label: "വിളയിനം:",
    followup_label: "ഇത് മുൻ കേസിലെ ഫോളോ-അപ്പ് റിക്കവറി ഫോട്ടോയാണ്",
    history_link: "📋 എന്റെ മുൻകാല പരിശോധനകൾ",
    logout: "ലോഗ് ഔട്ട് ചെയ്യുക",
    active_alert_title: "പ്രാദേശിക രോഗ മുന്നറിയിപ്പ്",
    active_alert_sub: "നിങ്ങളുടെ പ്രദേശത്ത് രോഗസാധ്യത കണ്ടെത്തി. പരിഹാരങ്ങൾക്ക് ഇവിടെ തൊടുക.",
    speak_prompt: "ശ്രദ്ധിക്കുന്നു... വിള ലക്ഷണങ്ങൾ പറയുക.",
  }
};

function applyLanguage(lang) {
  if (!TRANSLATIONS[lang]) lang = 'en';
  localStorage.setItem('cropguard_lang', lang);
  const dict = TRANSLATIONS[lang];

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (dict[key]) {
      if (el.tagName === 'INPUT' && el.getAttribute('type') === 'text') {
        el.placeholder = dict[key];
      } else {
        el.innerHTML = dict[key];
      }
    }
  });

  const langSelect = document.getElementById('langSwitcher');
  if (langSelect) langSelect.value = lang;
}

document.addEventListener('DOMContentLoaded', () => {
  const savedLang = localStorage.getItem('cropguard_lang') || 'en';
  applyLanguage(savedLang);
});
