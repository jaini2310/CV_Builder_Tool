import { CommonModule } from "@angular/common";
import { Component, OnInit } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { ApiService } from "./api.service";
import { ChatMessage, CvTemplateId, ExportFormat, StructuredCv, SupportedLanguage } from "./models";

type TranslationKey =
  | "initialAssistantMessage"
  | "loadingTitle"
  | "loadingCopy"
  | "reviewingResume"
  | "reviewingResumeCopy"
  | "editCvFields"
  | "editCvCopy"
  | "close"
  | "careerObjective"
  | "fullName"
  | "title"
  | "totalItExperience"
  | "contact"
  | "location"
  | "summary"
  | "skills"
  | "certifications"
  | "achievements"
  | "education"
  | "experience"
  | "addExperience"
  | "company"
  | "role"
  | "startDate"
  | "endDate"
  | "responsibilities"
  | "remove"
  | "at"
  | "onePerLine"
  | "commaOrNewLineSeparated"
  | "cancel"
  | "saveChanges"
  | "saving"
  | "siteTitle"
  | "siteSubtitle"
  | "tagVoice"
  | "tagExport"
  | "tagTemplate"
  | "language"
  | "profileCompletion"
  | "userResponses"
  | "skillsCaptured"
  | "experienceItems"
  | "conversationWorkspace"
  | "uploadResume"
  | "chooseResume"
  | "resumeSupported"
  | "assistantRole"
  | "userRole"
  | "typeYourAnswer"
  | "recording"
  | "microphone"
  | "send"
  | "failedToGetNextQuestion"
  | "couldNotRefreshPreview"
  | "resumeImportFailed"
  | "resumeReviewedPrefix"
  | "resumeReviewedSuffix"
  | "cvSnapshot"
  | "editCv"
  | "template"
  | "exportFormat"
  | "docxNote"
  | "refreshPreview"
  | "generate"
  | "generating"
  | "uploadPhoto"
  | "choosePhoto"
  | "photoSupported"
  | "removePhoto"
  | "candidateNamePending"
  | "currentTitlePending"
  | "totalItExperiencePrefix"
  | "summaryPending"
  | "rolePending"
  | "companyPending"
  | "generatedFileEmpty"
  | "cvGenerationFailed"
  | "couldNotSaveCvChanges"
  | "connectingMicrophone"
  | "transcribingAnswer"
  | "listeningAnswer"
  | "recordingStarted"
  | "microphoneCouldNotStart"
  | "noSpeechCaptured"
  | "transcriptAdded"
  | "noClearSpeech"
  | "audioTranscriptionFailed"
  | "selectLanguageToCreateCv"
  | "convertingPreview"
  | "customTitle"
  | "customDescription"
  | "postcardTitle"
  | "postcardDescription"
  | "sampleTitle"
  | "sampleDescription";

const LANGUAGE_OPTIONS: Array<{ code: SupportedLanguage; label: string; apiLabel: string }> = [
  { code: "en", label: "English", apiLabel: "English" },
  { code: "de", label: "Deutsch", apiLabel: "German" },
  { code: "es", label: "Espanol", apiLabel: "Spanish" },
  { code: "ja", label: "Japanese", apiLabel: "Japanese" },
];  

const OUTPUT_LANGUAGE_OPTIONS = LANGUAGE_OPTIONS.filter((option) => ["en", "de", "es"].includes(option.code));

const UI_STRINGS: Record<SupportedLanguage, Record<TranslationKey, string>> = {
  en: {
    initialAssistantMessage: "Hi! I will help you create your CV in NTT Data format.\n\nWhat is your full name?",
    loadingTitle: "Loading CV Studio",
    loadingCopy: "Preparing the workspace and templates.",
    reviewingResume: "Reviewing your resume",
    reviewingResumeCopy: "Extracting content, structuring the CV, and preparing follow-up questions.",
    editCvFields: "Edit CV fields",
    editCvCopy: "Update the preview directly without typing a chat prompt.",
    close: "Close",
    careerObjective: "Career objective",
    fullName: "Full name",
    title: "Title",
    totalItExperience: "Total IT experience",
    contact: "Contact",
    location: "Location",
    summary: "Summary",
    skills: "Skills",
    certifications: "Certifications",
    achievements: "Achievements",
    education: "Education",
    experience: "Experience",
    addExperience: "Add Experience",
    company: "Company",
    role: "Role",
    startDate: "Start date",
    endDate: "End date",
    responsibilities: "Responsibilities",
    remove: "Remove",
    at: "at",
    onePerLine: "One per line",
    commaOrNewLineSeparated: "Comma or new line separated",
    cancel: "Cancel",
    saveChanges: "Save Changes",
    saving: "Saving...",
    siteTitle: "NTT DATA Internal CV Studio",
    siteSubtitle: "Build consultant profiles, capture structured details, and export polished resumes.",
    tagVoice: "Voice-assisted",
    tagExport: "DOCX + PDF",
    tagTemplate: "Template-ready",
    language: "Language",
    profileCompletion: "Profile completion",
    userResponses: "User responses",
    skillsCaptured: "Skills captured",
    experienceItems: "Experience items",
    conversationWorkspace: "Conversation Workspace",
    uploadResume: "Upload existing CV or resume",
    chooseResume: "Choose Resume",
    resumeSupported: "PDF or DOCX supported",
    assistantRole: "assistant",
    userRole: "user",
    typeYourAnswer: "Type your answer",
    recording: "Recording...",
    microphone: "Microphone",
    send: "Send",
    failedToGetNextQuestion: "Failed to get next question.",
    couldNotRefreshPreview: "Could not refresh CV preview.",
    resumeImportFailed: "Resume import failed.",
    resumeReviewedPrefix: "I reviewed your uploaded resume",
    resumeReviewedSuffix: " and mapped the available details into the CV workspace.",
    cvSnapshot: "CV Snapshot",
    editCv: "Edit CV",
    template: "Template",
    exportFormat: "Export format",
    docxNote: "DOCX currently uses the provided Word template. Postcard and Sample have distinct styled PDF layouts.",
    refreshPreview: "Refresh Preview",
    generate: "Generate",
    generating: "Generating",
    uploadPhoto: "Upload profile photo (optional)",
    choosePhoto: "Choose Photo",
    photoSupported: "PNG or JPG supported",
    removePhoto: "Remove Photo",
    candidateNamePending: "Candidate name pending",
    currentTitlePending: "Current title pending",
    totalItExperiencePrefix: "Total IT experience:",
    summaryPending: "Summary will appear here as conversation grows.",
    rolePending: "Role pending",
    companyPending: "Company pending",
    generatedFileEmpty: "Generated file was empty.",
    cvGenerationFailed: "CV generation failed.",
    couldNotSaveCvChanges: "Could not save CV changes.",
    connectingMicrophone: "Connecting microphone...",
    transcribingAnswer: "Transcribing your answer...",
    listeningAnswer: "Listening for your answer...",
    recordingStarted: "Recording...",
    microphoneCouldNotStart: "Microphone could not start. Check browser permission and device.",
    noSpeechCaptured: "No speech was captured. Please try again.",
    transcriptAdded: "Transcript added to the message box.",
    noClearSpeech: "No clear speech was detected. Please try again.",
    audioTranscriptionFailed: "Audio transcription failed.",
    selectLanguageToCreateCv: "Generate/Review CV In Preferred Language",
    convertingPreview: "Converting preview to the selected language...",
    customTitle: "Custom",
    customDescription: "Uses the provided NTT DATA resume structure.",
    postcardTitle: "Postcard",
    postcardDescription: "More visual, compact, and card-led summary layout.",
    sampleTitle: "Sample",
    sampleDescription: "Balanced modern sample layout for general sharing.",
  },
  de: {
    initialAssistantMessage: "Hallo! Ich helfe Ihnen dabei, Ihren Lebenslauf im NTT-DATA-Format zu erstellen.\n\nWie lautet Ihr vollstandiger Name?",
    loadingTitle: "CV Studio wird geladen",
    loadingCopy: "Arbeitsbereich und Vorlagen werden vorbereitet.",
    reviewingResume: "Ihr Lebenslauf wird gepruft",
    reviewingResumeCopy: "Inhalte werden extrahiert, der CV strukturiert und Folgefragen vorbereitet.",
    editCvFields: "CV-Felder bearbeiten",
    editCvCopy: "Aktualisieren Sie die Vorschau direkt, ohne einen Chat-Prompt zu schreiben.",
    close: "Schliessen",
    careerObjective: "Karriereziel",
    fullName: "Vollstandiger Name",
    title: "Titel",
    totalItExperience: "Gesamte IT-Erfahrung",
    contact: "Kontakt",
    location: "Standort",
    summary: "Zusammenfassung",
    skills: "Kenntnisse",
    certifications: "Zertifizierungen",
    achievements: "Erfolge",
    education: "Ausbildung",
    experience: "Berufserfahrung",
    addExperience: "Erfahrung hinzufugen",
    company: "Unternehmen",
    role: "Rolle",
    startDate: "Startdatum",
    endDate: "Enddatum",
    responsibilities: "Aufgaben",
    remove: "Entfernen",
    at: "bei",
    onePerLine: "Eine pro Zeile",
    commaOrNewLineSeparated: "Durch Komma oder Zeilenumbruch getrennt",
    cancel: "Abbrechen",
    saveChanges: "Anderungen speichern",
    saving: "Wird gespeichert...",
    siteTitle: "NTT DATA Interne CV Studio",
    siteSubtitle: "Erstellen Sie Beraterprofile, erfassen Sie strukturierte Details und exportieren Sie professionelle Lebenslaufe.",
    tagVoice: "Sprachgestutzt",
    tagExport: "DOCX + PDF",
    tagTemplate: "Vorlagenbereit",
    language: "Sprache",
    profileCompletion: "Profilfortschritt",
    userResponses: "Benutzerantworten",
    skillsCaptured: "Erfasste Kenntnisse",
    experienceItems: "Erfahrungseintrage",
    conversationWorkspace: "Gesprachebereich",
    uploadResume: "Vorhandenen CV oder Lebenslauf hochladen",
    chooseResume: "Lebenslauf auswahlen",
    resumeSupported: "PDF oder DOCX unterstutzt",
    assistantRole: "assistent",
    userRole: "benutzer",
    typeYourAnswer: "Antwort eingeben",
    recording: "Aufnahme...",
    microphone: "Mikrofon",
    send: "Senden",
    failedToGetNextQuestion: "Die nachste Frage konnte nicht geladen werden.",
    couldNotRefreshPreview: "Die CV-Vorschau konnte nicht aktualisiert werden.",
    resumeImportFailed: "Der Lebenslaufimport ist fehlgeschlagen.",
    resumeReviewedPrefix: "Ich habe Ihren hochgeladenen Lebenslauf",
    resumeReviewedSuffix: " gepruft und die verfugbaren Details in den CV-Arbeitsbereich ubernommen.",
    cvSnapshot: "CV-Vorschau",
    editCv: "CV bearbeiten",
    template: "Vorlage",
    exportFormat: "Exportformat",
    docxNote: "DOCX verwendet derzeit die bereitgestellte Word-Vorlage. Postcard und Sample haben unterschiedliche PDF-Layouts.",
    refreshPreview: "Vorschau aktualisieren",
    generate: "Erstellen",
    generating: "Wird erstellt",
    uploadPhoto: "Profilfoto hochladen (optional)",
    choosePhoto: "Foto auswahlen",
    photoSupported: "PNG oder JPG unterstutzt",
    removePhoto: "Foto entfernen",
    candidateNamePending: "Name des Kandidaten steht aus",
    currentTitlePending: "Aktueller Titel steht aus",
    totalItExperiencePrefix: "Gesamte IT-Erfahrung:",
    summaryPending: "Die Zusammenfassung wird angezeigt, sobald das Gesprach fortschreitet.",
    rolePending: "Rolle ausstehend",
    companyPending: "Unternehmen ausstehend",
    generatedFileEmpty: "Die erzeugte Datei war leer.",
    cvGenerationFailed: "Die CV-Erstellung ist fehlgeschlagen.",
    couldNotSaveCvChanges: "CV-Anderungen konnten nicht gespeichert werden.",
    connectingMicrophone: "Mikrofon wird verbunden...",
    transcribingAnswer: "Ihre Antwort wird transkribiert...",
    listeningAnswer: "Ihre Antwort wird aufgenommen...",
    recordingStarted: "Aufnahme...",
    microphoneCouldNotStart: "Das Mikrofon konnte nicht gestartet werden. Uberprufen Sie Browserberechtigung und Gerat.",
    noSpeechCaptured: "Es wurde keine Sprache aufgenommen. Bitte versuchen Sie es erneut.",
    transcriptAdded: "Das Transkript wurde in das Nachrichtenfeld eingefugt.",
    noClearSpeech: "Keine deutliche Sprache erkannt. Bitte versuchen Sie es erneut.",
    audioTranscriptionFailed: "Die Audiotranskription ist fehlgeschlagen.",
    selectLanguageToCreateCv: "CV in der bevorzugten Sprache erstellen/anzeigen",
    convertingPreview: "Die Vorschau wird in die ausgewahlte Sprache umgewandelt...",
    customTitle: "Benutzerdefiniert",
    customDescription: "Verwendet die bereitgestellte NTT-DATA-Lebenslaufstruktur.",
    postcardTitle: "Postkarte",
    postcardDescription: "Visueller, kompakter und kartenbasierter Aufbau.",
    sampleTitle: "Beispiel",
    sampleDescription: "Ausgewogenes modernes Beispiel-Layout fur allgemeine Weitergabe.",
  },
  es: {
    initialAssistantMessage: "Hola. Le ayudare a crear su CV en el formato de NTT Data.\n\nCual es su nombre completo?",
    loadingTitle: "Cargando CV Studio",
    loadingCopy: "Preparando el espacio de trabajo y las plantillas.",
    reviewingResume: "Revisando su curriculo",
    reviewingResumeCopy: "Extrayendo contenido, estructurando el CV y preparando preguntas de seguimiento.",
    editCvFields: "Editar campos del CV",
    editCvCopy: "Actualice la vista previa directamente sin escribir un mensaje en el chat.",
    close: "Cerrar",
    careerObjective: "Objetivo profesional",
    fullName: "Nombre completo",
    title: "Titulo",
    totalItExperience: "Experiencia total en TI",
    contact: "Contacto",
    location: "Ubicacion",
    summary: "Resumen",
    skills: "Habilidades",
    certifications: "Certificaciones",
    achievements: "Logros",
    education: "Educacion",
    experience: "Experiencia",
    addExperience: "Agregar experiencia",
    company: "Empresa",
    role: "Rol",
    startDate: "Fecha de inicio",
    endDate: "Fecha de fin",
    responsibilities: "Responsabilidades",
    remove: "Eliminar",
    at: "en",
    onePerLine: "Una por linea",
    commaOrNewLineSeparated: "Separado por coma o salto de linea",
    cancel: "Cancelar",
    saveChanges: "Guardar cambios",
    saving: "Guardando...",
    siteTitle: "NTT DATA CV Studio Interno",
    siteSubtitle: "Cree perfiles de consultores, capture detalles estructurados y exporte curriculos pulidos.",
    tagVoice: "Asistido por voz",
    tagExport: "DOCX + PDF",
    tagTemplate: "Listo para plantillas",
    language: "Idioma",
    profileCompletion: "Completitud del perfil",
    userResponses: "Respuestas del usuario",
    skillsCaptured: "Habilidades capturadas",
    experienceItems: "Elementos de experiencia",
    conversationWorkspace: "Espacio de conversacion",
    uploadResume: "Cargar CV o curriculo existente",
    chooseResume: "Elegir curriculo",
    resumeSupported: "Compatible con PDF o DOCX",
    assistantRole: "asistente",
    userRole: "usuario",
    typeYourAnswer: "Escriba su respuesta",
    recording: "Grabando...",
    microphone: "Microfono",
    send: "Enviar",
    failedToGetNextQuestion: "No se pudo obtener la siguiente pregunta.",
    couldNotRefreshPreview: "No se pudo actualizar la vista previa del CV.",
    resumeImportFailed: "La importacion del curriculo fallo.",
    resumeReviewedPrefix: "Revise su curriculo cargado",
    resumeReviewedSuffix: " y asigne los detalles disponibles al espacio de trabajo del CV.",
    cvSnapshot: "Vista previa del CV",
    editCv: "Editar CV",
    template: "Plantilla",
    exportFormat: "Formato de exportacion",
    docxNote: "DOCX usa actualmente la plantilla de Word proporcionada. Postcard y Sample tienen disenos PDF distintos.",
    refreshPreview: "Actualizar vista previa",
    generate: "Generar",
    generating: "Generando",
    uploadPhoto: "Cargar foto de perfil (opcional)",
    choosePhoto: "Elegir foto",
    photoSupported: "Compatible con PNG o JPG",
    removePhoto: "Eliminar foto",
    candidateNamePending: "Nombre del candidato pendiente",
    currentTitlePending: "Titulo actual pendiente",
    totalItExperiencePrefix: "Experiencia total en TI:",
    summaryPending: "El resumen aparecera aqui a medida que avance la conversacion.",
    rolePending: "Rol pendiente",
    companyPending: "Empresa pendiente",
    generatedFileEmpty: "El archivo generado estaba vacio.",
    cvGenerationFailed: "La generacion del CV fallo.",
    couldNotSaveCvChanges: "No se pudieron guardar los cambios del CV.",
    connectingMicrophone: "Conectando microfono...",
    transcribingAnswer: "Transcribiendo su respuesta...",
    listeningAnswer: "Escuchando su respuesta...",
    recordingStarted: "Grabando...",
    microphoneCouldNotStart: "No se pudo iniciar el microfono. Revise el permiso del navegador y el dispositivo.",
    noSpeechCaptured: "No se capturo voz. Intente nuevamente.",
    transcriptAdded: "La transcripcion se agrego al cuadro de mensaje.",
    noClearSpeech: "No se detecto voz clara. Intente nuevamente.",
    audioTranscriptionFailed: "La transcripcion de audio fallo.",
    selectLanguageToCreateCv: "Generar/Revisar CV en el idioma preferido",
    convertingPreview: "Convirtiendo la vista previa al idioma seleccionado...",
    customTitle: "Personalizado",
    customDescription: "Usa la estructura de curriculo de NTT DATA proporcionada.",
    postcardTitle: "Postal",
    postcardDescription: "Diseno mas visual, compacto y basado en tarjetas.",
    sampleTitle: "Ejemplo",
    sampleDescription: "Diseno moderno equilibrado para uso general.",
  },
  hi: {
    initialAssistantMessage: "Namaste. Main NTT Data format mein aapka CV banane mein madad karunga.\n\nAapka poora naam kya hai?",
    loadingTitle: "CV Studio load ho raha hai",
    loadingCopy: "Workspace aur templates taiyar kiye ja rahe hain.",
    reviewingResume: "Aapka resume review ho raha hai",
    reviewingResumeCopy: "Content extract ho raha hai, CV structure ban raha hai, aur follow-up questions taiyar ho rahe hain.",
    editCvFields: "CV fields edit karein",
    editCvCopy: "Chat prompt likhe bina preview ko seedha update karein.",
    close: "Band karein",
    careerObjective: "Career objective",
    fullName: "Poora naam",
    title: "Title",
    totalItExperience: "Kul IT experience",
    contact: "Contact",
    location: "Location",
    summary: "Summary",
    skills: "Skills",
    certifications: "Certifications",
    achievements: "Achievements",
    education: "Education",
    experience: "Experience",
    addExperience: "Experience jodein",
    company: "Company",
    role: "Role",
    startDate: "Start date",
    endDate: "End date",
    responsibilities: "Responsibilities",
    remove: "Remove",
    at: "at",
    onePerLine: "Har line mein ek",
    commaOrNewLineSeparated: "Comma ya new line se alag karein",
    cancel: "Cancel",
    saveChanges: "Changes save karein",
    saving: "Save ho raha hai...",
    siteTitle: "NTT DATA Internal CV Studio",
    siteSubtitle: "Consultant profiles banayein, structured details capture karein, aur polished resumes export karein.",
    tagVoice: "Voice-assisted",
    tagExport: "DOCX + PDF",
    tagTemplate: "Template-ready",
    language: "Bhasha",
    profileCompletion: "Profile completion",
    userResponses: "User responses",
    skillsCaptured: "Skills captured",
    experienceItems: "Experience items",
    conversationWorkspace: "Conversation Workspace",
    uploadResume: "Existing CV ya resume upload karein",
    chooseResume: "Resume chunein",
    resumeSupported: "PDF ya DOCX supported",
    assistantRole: "assistant",
    userRole: "user",
    typeYourAnswer: "Apna jawab type karein",
    recording: "Recording...",
    microphone: "Microphone",
    send: "Send",
    failedToGetNextQuestion: "Agla question nahin mil saka.",
    couldNotRefreshPreview: "CV preview refresh nahin ho saka.",
    resumeImportFailed: "Resume import fail ho gaya.",
    resumeReviewedPrefix: "Maine aapka uploaded resume",
    resumeReviewedSuffix: " review karke available details ko CV workspace mein map kar diya hai.",
    cvSnapshot: "CV Snapshot",
    editCv: "CV edit karein",
    template: "Template",
    exportFormat: "Export format",
    docxNote: "DOCX abhi provided Word template ka use karta hai. Postcard aur Sample ke alag PDF layouts hain.",
    refreshPreview: "Preview refresh karein",
    generate: "Generate",
    generating: "Generate ho raha hai",
    uploadPhoto: "Profile photo upload karein (optional)",
    choosePhoto: "Photo chunein",
    photoSupported: "PNG ya JPG supported",
    removePhoto: "Photo hataein",
    candidateNamePending: "Candidate name pending",
    currentTitlePending: "Current title pending",
    totalItExperiencePrefix: "Kul IT experience:",
    summaryPending: "Conversation badhne par summary yahan dikhegi.",
    rolePending: "Role pending",
    companyPending: "Company pending",
    generatedFileEmpty: "Generated file empty thi.",
    cvGenerationFailed: "CV generation fail ho gaya.",
    couldNotSaveCvChanges: "CV changes save nahin ho sake.",
    connectingMicrophone: "Microphone connect ho raha hai...",
    transcribingAnswer: "Aapka jawab transcribe ho raha hai...",
    listeningAnswer: "Aapka jawab suna ja raha hai...",
    recordingStarted: "Recording...",
    microphoneCouldNotStart: "Microphone start nahin ho saka. Browser permission aur device check karein.",
    noSpeechCaptured: "Speech capture nahin hui. Dobara try karein.",
    transcriptAdded: "Transcript message box mein add kar diya gaya hai.",
    noClearSpeech: "Clear speech detect nahin hui. Dobara try karein.",
    audioTranscriptionFailed: "Audio transcription fail ho gaya.",
    selectLanguageToCreateCv: "Pasandida language mein CV generate/review karein",
    convertingPreview: "Preview selected language mein convert ho raha hai...",
    customTitle: "Custom",
    customDescription: "Provided NTT DATA resume structure ka use karta hai.",
    postcardTitle: "Postcard",
    postcardDescription: "Zyada visual, compact, aur card-based summary layout.",
    sampleTitle: "Sample",
    sampleDescription: "General sharing ke liye balanced modern sample layout.",
  },
  ja: {
    initialAssistantMessage: "こんにちは。NTT Data形式のCV作成をお手伝いします。\n\nフルネームを教えてください。",
    loadingTitle: "CV Studioを読み込み中",
    loadingCopy: "ワークスペースとテンプレートを準備しています。",
    reviewingResume: "履歴書を確認しています",
    reviewingResumeCopy: "内容を抽出し、CVを構造化し、次の質問を準備しています。",
    editCvFields: "CV項目を編集",
    editCvCopy: "チャットで指示を入力せずに、プレビューを直接更新できます。",
    close: "閉じる",
    careerObjective: "キャリア目標",
    fullName: "氏名",
    title: "役職",
    totalItExperience: "総IT経験年数",
    contact: "連絡先",
    location: "所在地",
    summary: "概要",
    skills: "スキル",
    certifications: "認定資格",
    achievements: "実績",
    education: "学歴",
    experience: "職務経験",
    addExperience: "経験を追加",
    company: "会社名",
    role: "役割",
    startDate: "開始日",
    endDate: "終了日",
    responsibilities: "担当業務",
    remove: "削除",
    at: "at",
    onePerLine: "1行に1件",
    commaOrNewLineSeparated: "カンマまたは改行で区切ってください",
    cancel: "キャンセル",
    saveChanges: "変更を保存",
    saving: "保存中...",
    siteTitle: "NTT DATA Internal CV Studio",
    siteSubtitle: "コンサルタントのプロフィールを作成し、構造化された情報を収集し、整った履歴書を出力します。",
    tagVoice: "音声対応",
    tagExport: "DOCX + PDF",
    tagTemplate: "テンプレート対応",
    language: "言語",
    profileCompletion: "プロフィール完成度",
    userResponses: "ユーザー回答数",
    skillsCaptured: "取得済みスキル",
    experienceItems: "経験件数",
    conversationWorkspace: "会話ワークスペース",
    uploadResume: "既存のCVまたは履歴書をアップロード",
    chooseResume: "履歴書を選択",
    resumeSupported: "PDFまたはDOCXに対応",
    assistantRole: "assistant",
    userRole: "user",
    typeYourAnswer: "回答を入力してください",
    recording: "録音中...",
    microphone: "マイク",
    send: "送信",
    failedToGetNextQuestion: "次の質問を取得できませんでした。",
    couldNotRefreshPreview: "CVプレビューを更新できませんでした。",
    resumeImportFailed: "履歴書の取り込みに失敗しました。",
    resumeReviewedPrefix: "アップロードされた履歴書",
    resumeReviewedSuffix: " を確認し、利用可能な情報をCVワークスペースに反映しました。",
    cvSnapshot: "CVプレビュー",
    editCv: "CVを編集",
    template: "テンプレート",
    exportFormat: "出力形式",
    docxNote: "DOCXは現在、提供されたWordテンプレートを使用します。PostcardとSampleはPDFのみ異なるレイアウトです。",
    refreshPreview: "プレビューを更新",
    generate: "生成",
    generating: "生成中",
    uploadPhoto: "プロフィール写真をアップロード（任意）",
    choosePhoto: "写真を選択",
    photoSupported: "PNGまたはJPGに対応",
    removePhoto: "写真を削除",
    candidateNamePending: "候補者名は未入力です",
    currentTitlePending: "現在の役職は未入力です",
    totalItExperiencePrefix: "総IT経験年数:",
    summaryPending: "会話が進むと概要がここに表示されます。",
    rolePending: "役割未入力",
    companyPending: "会社名未入力",
    generatedFileEmpty: "生成されたファイルが空でした。",
    cvGenerationFailed: "CV生成に失敗しました。",
    couldNotSaveCvChanges: "CVの変更を保存できませんでした。",
    connectingMicrophone: "マイクに接続しています...",
    transcribingAnswer: "回答を文字起こししています...",
    listeningAnswer: "回答を聞き取っています...",
    recordingStarted: "録音中...",
    microphoneCouldNotStart: "マイクを開始できませんでした。ブラウザ権限とデバイスを確認してください。",
    noSpeechCaptured: "音声を取得できませんでした。もう一度お試しください。",
    transcriptAdded: "文字起こし結果を入力欄に追加しました。",
    noClearSpeech: "明確な音声を検出できませんでした。もう一度お試しください。",
    audioTranscriptionFailed: "音声文字起こしに失敗しました。",
    selectLanguageToCreateCv: "希望する言語でCVを生成/確認",
    convertingPreview: "プレビューを選択した言語に変換しています...",
    customTitle: "Custom",
    customDescription: "提供されたNTT DATA履歴書構成を使用します。",
    postcardTitle: "Postcard",
    postcardDescription: "より視覚的でコンパクトなカード型サマリーレイアウトです。",
    sampleTitle: "Sample",
    sampleDescription: "一般共有向けのバランスの取れたモダンなレイアウトです。",
  },
};

function getInitialAssistantMessage(language: SupportedLanguage): string {
  return UI_STRINGS[language].initialAssistantMessage;
}

@Component({
  selector: "app-root",
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: "./app.component.html",
})
export class AppComponent implements OnInit {
  private static readonly EMPTY_EXPERIENCE = {
    company: "",
    role: "",
    start_date: "",
    end_date: "",
    responsibilitiesText: "",
  };

  selectedLanguage: SupportedLanguage = "en";
  selectedOutputLanguage: SupportedLanguage = "en";
  readonly languageOptions = LANGUAGE_OPTIONS;
  readonly outputLanguageOptions = OUTPUT_LANGUAGE_OPTIONS;
  messages: ChatMessage[] = [
    {
      role: "assistant",
      content: getInitialAssistantMessage("en"),
    },
  ];

  composerText = "";
  isBusy = false;
  isConnectingMic = false;
  isRecording = false;
  isTranscribingAudio = false;
  isGeneratingCv = false;
  isImportingResume = false;
  isEditingCv = false;
  isSavingCv = false;
  isTranslatingPreview = false;
  chatError = "";
  previewError = "";
  audioNotice = "";
  interimTranscript = "";
  latestTranscript = "";
  micSupported = this.isMicAvailable();
  selectedTemplate: CvTemplateId = "custom";
  selectedExportFormat: ExportFormat = "pdf";
  isPageLoading = true;

  structuredCv: StructuredCv | null = null;
  previewCv: StructuredCv | null = null;
  previewCvTranslatedLanguage: SupportedLanguage | null = null;
  editDraft = this.createEmptyEditDraft();
  profilePhotoBase64 = "";
  profilePhotoName = "";
  importedResumeName = "";
  photoOfferMade = false;
  readonly templateOptions: CvTemplateId[] = ["custom", "postcard", "sample"];

  private micStream: MediaStream | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private recordedChunks: Blob[] = [];
  private recordingMimeType = "audio/webm";
  private micToggleCooldownUntil = 0;
  private baseComposerText = "";

  constructor(private readonly api: ApiService) {}

  ngOnInit(): void {
    setTimeout(() => {
      this.isPageLoading = false;
    }, 1000);
  }

  get userResponses(): number {
    return this.messages.filter((m) => m.role === "user").length;
  }

  get completion(): number {
    if (!this.structuredCv) {
      return 0;
    }
    const checks = [
      !!this.structuredCv.name,
      !!this.structuredCv.title,
      !!this.structuredCv.total_it_experience,
      !!this.structuredCv.summary,
      !!this.structuredCv.skills?.length,
      !!this.structuredCv.experience?.length,
      !!this.structuredCv.education?.length,
      !!this.structuredCv.achievements?.length,
    ];
    const completed = checks.filter(Boolean).length;
    return Math.round((completed / checks.length) * 100);
  }

  get skillsCount(): number {
    return this.structuredCv?.skills?.length ?? 0;
  }

  get experienceCount(): number {
    return this.structuredCv?.experience?.length ?? 0;
  }

  get selectedLanguageLabel(): string {
    return this.languageOptions.find((option) => option.code === this.selectedLanguage)?.apiLabel || "English";
  }

  get selectedOutputLanguageLabel(): string {
    return this.outputLanguageOptions.find((option) => option.code === this.selectedOutputLanguage)?.apiLabel || "English";
  }

  get renderedCv(): StructuredCv | null {
    return this.previewCv || this.structuredCv;
  }

  get hasPreviewContent(): boolean {
    const structured = this.renderedCv;
    if (!structured) {
      return false;
    }

    return [
      structured.objectives,
      structured.name,
      structured.title,
      structured.total_it_experience,
      structured.contact,
      structured.location,
      structured.summary,
      ...(structured.skills || []),
      ...(structured.certifications || []),
      ...(structured.achievements || []),
      ...this.asDisplayList(structured.education || []),
      ...((structured.experience || []).flatMap((item) => [
        item.company || "",
        item.role || "",
        item.start_date || "",
        item.end_date || "",
        ...((item.responsibilities || []) as string[]),
      ])),
    ].some((value) => !!String(value || "").trim());
  }

  get micStatusText(): string {
    if (this.isConnectingMic) {
      return this.t("connectingMicrophone");
    }
    if (this.isTranscribingAudio) {
      return this.t("transcribingAnswer");
    }
    if (this.isRecording) {
      return this.t("listeningAnswer");
    }
    return "";
  }

  t(key: TranslationKey): string {
    return UI_STRINGS[this.selectedLanguage][key] || UI_STRINGS.en[key] || key;
  }

  previewT(key: TranslationKey): string {
    return UI_STRINGS[this.selectedOutputLanguage][key] || UI_STRINGS.en[key] || key;
  }

  getTemplateTitle(templateId: CvTemplateId): string {
    if (templateId === "custom") {
      return this.t("customTitle");
    }
    if (templateId === "postcard") {
      return this.t("postcardTitle");
    }
    return this.t("sampleTitle");
  }

  getTemplateDescription(templateId: CvTemplateId): string {
    if (templateId === "custom") {
      return this.t("customDescription");
    }
    if (templateId === "postcard") {
      return this.t("postcardDescription");
    }
    return this.t("sampleDescription");
  }

  getRoleLabel(role: ChatMessage["role"]): string {
    return role === "assistant" ? this.t("assistantRole") : this.t("userRole");
  }

  onLanguageChange(): void {
    if (
      !this.userResponses &&
      this.messages.length === 1 &&
      this.messages[0].role === "assistant"
    ) {
      this.messages = [{ role: "assistant", content: getInitialAssistantMessage(this.selectedLanguage) }];
    }
  }

  onOutputLanguageChange(): void {
    if (!this.structuredCv) {
      this.previewCv = null;
      this.previewCvTranslatedLanguage = null;
      this.isTranslatingPreview = false;
      return;
    }

    this.previewError = "";
    this.isTranslatingPreview = false;

    if (this.previewCvTranslatedLanguage && this.previewCvTranslatedLanguage !== this.selectedOutputLanguage) {
      this.previewCv = this.structuredCv;
      this.previewCvTranslatedLanguage = null;
    }
  }

  sendMessage(): void {
    const cleaned = this.composerText.trim();
    if (!cleaned || this.isBusy || this.isConnectingMic || this.isRecording) {
      return;
    }

    this.chatError = "";
    this.audioNotice = "";
    this.messages.push({ role: "user", content: cleaned });
    this.composerText = "";
    this.latestTranscript = "";
    this.isBusy = true;

    this.api
      .getNextQuestion(this.messages, this.structuredCv, !!this.profilePhotoBase64, this.photoOfferMade, this.selectedLanguageLabel)
      .subscribe({
        next: (res) => {
          const question = (res.question || "").trim();
          if (question) {
            this.messages.push({ role: "assistant", content: question });
            if (question.toLowerCase().includes("photo")) {
              this.photoOfferMade = true;
            }
          }
          this.refreshPreview();
        },
        error: (err) => {
          this.chatError = err?.error?.detail || this.t("failedToGetNextQuestion");
          this.isBusy = false;
        },
      });
  }

  refreshPreview(translatePreview = false): void {
    const conversationText = this.buildConversationText();
    if (!conversationText.trim()) {
      this.previewError = "";
      if (this.structuredCv) {
        this.previewCv = this.structuredCv;
        this.previewCvTranslatedLanguage = null;
        if (translatePreview) {
          this.syncPreviewCv(
            () => {
              this.isBusy = false;
            },
            () => {
              this.isBusy = false;
            },
          );
          return;
        }
      }
      this.isBusy = false;
      this.isTranslatingPreview = false;
      return;
    }

    this.api.extractCv(conversationText, this.structuredCv).subscribe({
      next: (res) => {
        this.structuredCv = res.structured_cv;
        this.previewCv = this.structuredCv;
        this.previewCvTranslatedLanguage = null;
        this.previewError = "";
        if (translatePreview) {
          this.syncPreviewCv(
            () => {
              this.isBusy = false;
            },
            () => {
              this.isBusy = false;
            },
          );
          return;
        }
        this.isBusy = false;
        this.isTranslatingPreview = false;
      },
      error: (err) => {
        this.previewError = err?.error?.detail || this.t("couldNotRefreshPreview");
        this.isBusy = false;
      },
    });
  }

  onPhotoSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }

    this.profilePhotoName = file.name;
    this.photoOfferMade = true;

    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const base64 = result.includes(",") ? result.split(",")[1] : "";
      this.profilePhotoBase64 = base64;
    };
    reader.readAsDataURL(file);
  }

  onResumeSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) {
      return;
    }
    input.value = "";

    this.isBusy = true;
    this.isImportingResume = true;
    this.chatError = "";
    this.previewError = "";
    this.audioNotice = "";

    this.api.importResume(file, this.selectedLanguageLabel).subscribe({
      next: (res) => {
        this.structuredCv = res.structured_cv;
        this.previewCv = this.structuredCv;
        this.previewCvTranslatedLanguage = null;
        this.importedResumeName = res.file_name || file.name;
        this.photoOfferMade = false;
        this.messages = [
          {
            role: "assistant",
            content: `${this.t("resumeReviewedPrefix")}${this.importedResumeName ? ` (${this.importedResumeName})` : ""}${this.t("resumeReviewedSuffix")}`,
          },
        ];

        const question = (res.next_question || "").trim();
        if (question) {
          this.messages.push({ role: "assistant", content: question });
          if (question.toLowerCase().includes("photo")) {
            this.photoOfferMade = true;
          }
        }

        this.composerText = "";
        this.latestTranscript = "";
        this.isBusy = false;
        this.isImportingResume = false;
        this.isTranslatingPreview = false;
      },
      error: (err) => {
        this.chatError = err?.error?.detail || this.t("resumeImportFailed");
        this.isBusy = false;
        this.isImportingResume = false;
      },
    });
  }

  clearPhoto(): void {
    this.profilePhotoBase64 = "";
    this.profilePhotoName = "";
  }

  openEditCv(): void {
    const structured = this.renderedCv || this.structuredCv || {};
    this.editDraft = {
      objectives: structured.objectives || "",
      name: structured.name || "",
      title: structured.title || "",
      total_it_experience: structured.total_it_experience || "",
      contact: structured.contact || "",
      location: structured.location || "",
      summary: structured.summary || "",
      skillsText: (structured.skills || []).join(", "),
      certificationsText: (structured.certifications || []).join("\n"),
      achievementsText: (structured.achievements || []).join("\n"),
      educationText: this.asDisplayList(structured.education || []).join("\n"),
      experienceDrafts: (structured.experience || []).map((item) => ({
        company: item.company || "",
        role: item.role || "",
        start_date: item.start_date || "",
        end_date: item.end_date || "",
        responsibilitiesText: (item.responsibilities || []).join("\n"),
      })),
    };
    if (!this.editDraft.experienceDrafts.length) {
      this.addExperienceDraft();
    }
    this.isEditingCv = true;
  }

  closeEditCv(): void {
    this.isEditingCv = false;
  }

  saveEditCv(): void {
    const baseCv = this.renderedCv || this.structuredCv || {};
    const editingTranslatedPreview = !!this.previewCv && this.previewCvTranslatedLanguage !== null;
    const updated: StructuredCv = {
      ...baseCv,
      objectives: this.editDraft.objectives.trim(),
      name: this.editDraft.name.trim(),
      title: this.editDraft.title.trim(),
      total_it_experience: this.editDraft.total_it_experience.trim(),
      contact: this.editDraft.contact.trim(),
      location: this.editDraft.location.trim(),
      summary: this.editDraft.summary.trim(),
      skills: this.parseDelimitedList(this.editDraft.skillsText),
      certifications: this.parseLineList(this.editDraft.certificationsText),
      achievements: this.parseLineList(this.editDraft.achievementsText),
      education: this.parseLineList(this.editDraft.educationText),
      experience: this.editDraft.experienceDrafts
        .map((item) => ({
          company: item.company.trim(),
          role: item.role.trim(),
          start_date: item.start_date.trim(),
          end_date: item.end_date.trim(),
          responsibilities: this.parseLineList(item.responsibilitiesText),
        }))
        .filter((item) => item.company || item.role || item.start_date || item.end_date || item.responsibilities?.length),
    };
    this.isSavingCv = true;
    this.previewError = "";
    this.chatError = "";

      this.api.saveCv(updated).subscribe({
        next: (res) => {
          this.structuredCv = res.structured_cv;
          this.previewCv = this.structuredCv;
          this.previewCvTranslatedLanguage = editingTranslatedPreview ? this.selectedOutputLanguage : null;
          this.isSavingCv = false;
          this.isEditingCv = false;
          this.isTranslatingPreview = false;
      },
      error: (err) => {
        this.previewError = err?.error?.detail || this.t("couldNotSaveCvChanges");
        this.isSavingCv = false;
      },
    });
  }

  addExperienceDraft(): void {
    this.editDraft.experienceDrafts.push({ ...AppComponent.EMPTY_EXPERIENCE });
  }

  removeExperienceDraft(index: number): void {
    this.editDraft.experienceDrafts.splice(index, 1);
    if (!this.editDraft.experienceDrafts.length) {
      this.addExperienceDraft();
    }
  }

  async toggleMicRecording(): Promise<void> {
    const now = Date.now();
    if (now < this.micToggleCooldownUntil) {
      return;
    }
    this.micToggleCooldownUntil = now + 350;

    if (!this.micSupported || this.isBusy) {
      return;
    }

    if (this.isRecording) {
      this.stopMicRecording();
      return;
    }

    await this.startMicRecording();
  }

  generateCv(): void {
    if (this.isBusy || this.isConnectingMic || this.isRecording) {
      return;
    }

    const canReuseTranslatedPreview =
      !!this.previewCv &&
      this.previewCvTranslatedLanguage === this.selectedOutputLanguage;
    const structured = (canReuseTranslatedPreview ? this.previewCv : this.structuredCv) || {};
    this.isBusy = true;
    this.isGeneratingCv = true;
    this.chatError = "";

    this.api
      .generateCv({
        structured_cv: structured,
        conversation_text: this.buildConversationText(),
        profile_photo_base64: this.profilePhotoBase64 || undefined,
        file_name: this.getExportFileName(this.selectedExportFormat),
        export_format: this.selectedExportFormat,
        template_id: this.selectedTemplate,
        output_language: this.selectedOutputLanguageLabel,
        skip_translation: canReuseTranslatedPreview,
      })
      .subscribe({
        next: (response) => {
          const fallbackName = this.getExportFileName(this.selectedExportFormat);
          const headerName = this.extractFileName(response.headers.get("content-disposition"));
          const name = headerName || fallbackName;
          const blob = response.body;
          if (!blob) {
            this.chatError = this.t("generatedFileEmpty");
            this.isBusy = false;
            this.isGeneratingCv = false;
            return;
          }
          const url = window.URL.createObjectURL(blob);
          const anchor = document.createElement("a");
          anchor.href = url;
          anchor.download = name;
          anchor.click();
          window.URL.revokeObjectURL(url);
          this.isBusy = false;
          this.isGeneratingCv = false;
        },
        error: (err) => {
          this.chatError = err?.error?.detail || this.t("cvGenerationFailed");
          this.isBusy = false;
          this.isGeneratingCv = false;
        },
      });
  }

  asDisplayList(items: unknown[] | undefined): string[] {
    if (!items?.length) {
      return [];
    }
    return items
      .map((item) => {
        if (typeof item === "string") {
          return item.trim();
        }
        if (item && typeof item === "object" && !Array.isArray(item)) {
          const values = Object.values(item as Record<string, unknown>)
            .map((value) => String(value ?? "").trim())
            .filter((value) => !!value);
          return values.join(" | ");
        }
        return "";
      })
      .filter((item) => !!item);
  }

  private syncPreviewCv(onSuccess?: () => void, onError?: () => void): void {
    const source = this.structuredCv;
    if (!source) {
      this.previewCv = null;
      this.previewCvTranslatedLanguage = null;
      this.isTranslatingPreview = false;
      onSuccess?.();
      return;
    }

    this.isTranslatingPreview = true;
    this.api.translateCv(source, this.selectedOutputLanguageLabel).subscribe({
      next: (res) => {
        this.previewCv = res.structured_cv;
        this.previewCvTranslatedLanguage = this.selectedOutputLanguage;
        this.previewError = "";
        this.isTranslatingPreview = false;
        onSuccess?.();
      },
      error: (err) => {
        this.previewCv = source;
        this.previewCvTranslatedLanguage = null;
        this.previewError = err?.error?.detail || this.t("couldNotRefreshPreview");
        this.isTranslatingPreview = false;
        onError?.();
      },
    });
  }

  private buildConversationText(): string {
    return this.messages
      .filter((msg) => msg.role === "user")
      .map((msg) => `User: ${msg.content}`)
      .join("\n");
  }

  private getExportFileName(format: ExportFormat): string {
    const baseName = (this.structuredCv?.name || "candidate_cv")
      .trim()
      .replace(/[^a-zA-Z0-9_-]+/g, "_");
    return `${baseName || "candidate_cv"}.${format}`;
  }

  private isMicAvailable(): boolean {
    if (typeof window === "undefined" || typeof navigator === "undefined") {
      return false;
    }
    return typeof MediaRecorder !== "undefined" && !!navigator.mediaDevices?.getUserMedia;
  }

  private async startMicRecording(): Promise<void> {
    this.audioNotice = "";
    this.chatError = "";
    this.isConnectingMic = true;
    this.latestTranscript = "";
    this.baseComposerText = this.composerText.trim();
    this.recordedChunks = [];

    try {
      this.micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.recordingMimeType = this.pickRecordingMimeType();
      this.mediaRecorder = this.recordingMimeType
        ? new MediaRecorder(this.micStream, { mimeType: this.recordingMimeType })
        : new MediaRecorder(this.micStream);

      this.mediaRecorder.addEventListener("dataavailable", (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          this.recordedChunks.push(event.data);
        }
      });

      this.mediaRecorder.addEventListener("stop", () => {
        void this.transcribeRecordedAudio();
      });

      this.mediaRecorder.start(250);
      this.isConnectingMic = false;
      this.isRecording = true;
      this.audioNotice = this.t("recordingStarted");
    } catch {
      this.cleanupMicRecording();
      this.audioNotice = this.t("microphoneCouldNotStart");
    }
  }

  private stopMicRecording(): void {
    if (!this.mediaRecorder) {
      return;
    }

    this.isRecording = false;
    this.isBusy = true;
    this.isTranscribingAudio = true;
    this.audioNotice = this.t("transcribingAnswer");

    if (this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    } else {
      void this.transcribeRecordedAudio();
    }
  }

  private async transcribeRecordedAudio(): Promise<void> {
    const mimeType = this.mediaRecorder?.mimeType || this.recordingMimeType || "audio/webm";
    const extension = mimeType.includes("ogg") ? "ogg" : "webm";
    const audioBlob = new Blob(this.recordedChunks, { type: mimeType });

    this.cleanupMicRecording();

    if (!audioBlob.size) {
      this.audioNotice = this.t("noSpeechCaptured");
      this.isBusy = false;
      this.isTranscribingAudio = false;
      return;
    }

    const audioFile = new File([audioBlob], `speech.${extension}`, { type: mimeType });

    this.api.transcribeAudio(audioFile, this.selectedLanguage).subscribe({
      next: (res) => {
        this.latestTranscript = (res.transcript || "").trim();
        if (this.latestTranscript) {
          this.composerText = [this.baseComposerText, this.latestTranscript]
            .filter((part) => !!part)
            .join(" ")
            .trim();
          this.audioNotice = this.t("transcriptAdded");
        } else {
          this.audioNotice = this.t("noClearSpeech");
        }
        this.isBusy = false;
        this.isTranscribingAudio = false;
      },
      error: (err) => {
        this.audioNotice = err?.error?.detail || this.t("audioTranscriptionFailed");
        this.isBusy = false;
        this.isTranscribingAudio = false;
      },
    });
  }

  private cleanupMicRecording(): void {
    if (this.micStream) {
      this.micStream.getTracks().forEach((track) => track.stop());
      this.micStream = null;
    }

    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.isConnectingMic = false;
    this.isRecording = false;
  }

  private pickRecordingMimeType(): string {
    const preferredTypes = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"];
    return preferredTypes.find((type) => MediaRecorder.isTypeSupported(type)) || "";
  }

  private extractFileName(contentDisposition: string | null): string {
    if (!contentDisposition) {
      return "";
    }
    const match = contentDisposition.match(/filename="?([^"]+)"?/i);
    return match?.[1]?.trim() || "";
  }

  private createEmptyEditDraft() {
    return {
      objectives: "",
      name: "",
      title: "",
      total_it_experience: "",
      contact: "",
      location: "",
      summary: "",
      skillsText: "",
      certificationsText: "",
      achievementsText: "",
      educationText: "",
      experienceDrafts: [{ ...AppComponent.EMPTY_EXPERIENCE }],
    };
  }

  private parseDelimitedList(value: string): string[] {
    return value
      .split(/,|\n/)
      .map((item) => item.trim())
      .filter((item) => !!item);
  }

  private parseLineList(value: string): string[] {
    return value
      .split("\n")
      .map((item) => item.trim())
      .filter((item) => !!item);
  }
}
