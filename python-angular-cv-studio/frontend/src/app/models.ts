export interface ChatMessage {
  role: "assistant" | "user";
  content: string;
}

export type SupportedLanguage = "en" | "de" | "es" | "hi";
export type CvTemplateId = "custom" | "postcard" | "sample";
export type ExportFormat = "pdf" | "docx";

export interface ExperienceItem {
  company?: string;
  role?: string;
  start_date?: string;
  end_date?: string;
  responsibilities?: string[];
}

export interface StructuredCv {
  objectives?: string;
  name?: string;
  title?: string;
  total_it_experience?: string;
  contact?: string;
  location?: string;
  summary?: string;
  skills?: string[];
  experience?: ExperienceItem[];
  education?: Array<string | Record<string, unknown>>;
  achievements?: string[];
  certifications?: string[];
}
