import { Injectable } from "@angular/core";
import { HttpClient, HttpResponse } from "@angular/common/http";
import { Observable } from "rxjs";
import { ChatMessage, CvTemplateId, ExportFormat, StructuredCv } from "./models";

@Injectable({ providedIn: "root" })
export class ApiService {
  constructor(private readonly http: HttpClient) {}

  getNextQuestion(
    messages: ChatMessage[],
    hasProfilePhoto: boolean,
    photoOfferMade: boolean,
  ): Observable<{ question: string }> {
    return this.http.post<{ question: string }>("/api/next-question", {
      messages,
      has_profile_photo: hasProfilePhoto,
      photo_offer_made: photoOfferMade,
    });
  }

  extractCv(conversationText: string): Observable<{ structured_cv: StructuredCv | null }> {
    return this.http.post<{ structured_cv: StructuredCv | null }>("/api/extract-cv", {
      conversation_text: conversationText,
    });
  }

  transcribeAudio(file: File): Observable<{ transcript: string }> {
    const formData = new FormData();
    formData.append("audio_file", file);
    return this.http.post<{ transcript: string }>("/api/transcribe-audio", formData);
  }

  generateCv(payload: {
    structured_cv: StructuredCv;
    conversation_text?: string;
    profile_photo_base64?: string;
    file_name?: string;
    export_format: ExportFormat;
    template_id: CvTemplateId;
  }): Observable<HttpResponse<Blob>> {
    return this.http.post("/api/generate-cv", payload, {
      responseType: "blob",
      observe: "response",
    });
  }
}
