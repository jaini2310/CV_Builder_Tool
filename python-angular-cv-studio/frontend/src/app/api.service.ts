import { Injectable } from "@angular/core";
import { HttpClient, HttpResponse } from "@angular/common/http";
import { Observable } from "rxjs";
import { ChatMessage, CvTemplateId, ExportFormat, StructuredCv, SupportedLanguage } from "./models";

@Injectable({ providedIn: "root" })
export class ApiService {
  constructor(private readonly http: HttpClient) {}

  getNextQuestion(
    messages: ChatMessage[],
    structuredCv: StructuredCv | null,
    hasProfilePhoto: boolean,
    photoOfferMade: boolean,
    preferredLanguage: string,
  ): Observable<{ question: string }> {
    return this.http.post<{ question: string }>("/api/next-question", {
      messages,
      structured_cv: structuredCv || {},
      has_profile_photo: hasProfilePhoto,
      photo_offer_made: photoOfferMade,
      preferred_language: preferredLanguage,
    });
  }

  extractCv(conversationText: string, structuredCv: StructuredCv | null): Observable<{ structured_cv: StructuredCv | null }> {
    return this.http.post<{ structured_cv: StructuredCv | null }>("/api/extract-cv", {
      conversation_text: conversationText,
      structured_cv: structuredCv || {},
    });
  }

  saveCv(structuredCv: StructuredCv): Observable<{ structured_cv: StructuredCv }> {
    return this.http.post<{ structured_cv: StructuredCv }>("/api/save-cv", {
      structured_cv: structuredCv || {},
    });
  }

  translateCv(structuredCv: StructuredCv, targetLanguage: string): Observable<{ structured_cv: StructuredCv }> {
    return this.http.post<{ structured_cv: StructuredCv }>("/api/translate-cv", {
      structured_cv: structuredCv || {},
      target_language: targetLanguage,
    });
  }

  importResume(file: File, preferredLanguage: string): Observable<{ structured_cv: StructuredCv; next_question: string; file_name: string }> {
    const formData = new FormData();
    formData.append("resume_file", file);
    formData.append("preferred_language", preferredLanguage);
    return this.http.post<{ structured_cv: StructuredCv; next_question: string; file_name: string }>("/api/import-resume", formData);
  }

  transcribeAudio(file: File, transcriptionLanguage: SupportedLanguage): Observable<{ transcript: string }> {
    const formData = new FormData();
    formData.append("audio_file", file);
    formData.append("transcription_language", transcriptionLanguage);
    return this.http.post<{ transcript: string }>("/api/transcribe-audio", formData);
  }

  generateCv(payload: {
    structured_cv: StructuredCv;
    conversation_text?: string;
    profile_photo_base64?: string;
    file_name?: string;
    export_format: ExportFormat;
    template_id: CvTemplateId;
    output_language: string;
    skip_translation?: boolean;
  }): Observable<HttpResponse<Blob>> {
    return this.http.post("/api/generate-cv", payload, {
      responseType: "blob",
      observe: "response",
    });
  }
}
