import { CommonModule } from "@angular/common";
import { Component, OnInit } from "@angular/core";
import { FormsModule } from "@angular/forms";
import { ApiService } from "./api.service";
import { ChatMessage, CvTemplateId, ExportFormat, StructuredCv } from "./models";

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

  messages: ChatMessage[] = [
    {
      role: "assistant",
      content: "Hi! I will help you create your CV in NTT Data format.\n\nWhat is your full name?",
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
  editDraft = this.createEmptyEditDraft();
  profilePhotoBase64 = "";
  profilePhotoName = "";
  importedResumeName = "";
  photoOfferMade = false;
  readonly templateOptions: Array<{ id: CvTemplateId; title: string; description: string }> = [
    { id: "custom", title: "Custom", description: "Uses the provided NTT DATA resume structure." },
    { id: "postcard", title: "Postcard", description: "More visual, compact, and card-led summary layout." },
    { id: "sample", title: "Sample", description: "Balanced modern sample layout for general sharing." },
  ];

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

  get micStatusText(): string {
    if (this.isConnectingMic) {
      return "Connecting microphone...";
    }
    if (this.isTranscribingAudio) {
      return "Transcribing your answer...";
    }
    if (this.isRecording) {
      return "Listening for your answer...";
    }
    return "";
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
      .getNextQuestion(this.messages, this.structuredCv, !!this.profilePhotoBase64, this.photoOfferMade)
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
          this.chatError = err?.error?.detail || "Failed to get next question.";
          this.isBusy = false;
        },
      });
  }

  refreshPreview(): void {
    const conversationText = this.buildConversationText();
    if (!conversationText.trim()) {
      this.previewError = "";
      this.isBusy = false;
      return;
    }

    this.api.extractCv(conversationText, this.structuredCv).subscribe({
      next: (res) => {
        this.structuredCv = res.structured_cv;
        this.previewError = "";
        this.isBusy = false;
      },
      error: (err) => {
        this.previewError = err?.error?.detail || "Could not refresh CV preview.";
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

    this.api.importResume(file).subscribe({
      next: (res) => {
        this.structuredCv = res.structured_cv;
        this.importedResumeName = res.file_name || file.name;
        this.photoOfferMade = false;
        this.messages = [
          {
            role: "assistant",
            content: `I reviewed your uploaded resume${this.importedResumeName ? ` (${this.importedResumeName})` : ""} and mapped the available details into the CV workspace.`,
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
      },
      error: (err) => {
        this.chatError = err?.error?.detail || "Resume import failed.";
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
    const structured = this.structuredCv || {};
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
    const updated: StructuredCv = {
      ...(this.structuredCv || {}),
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
        this.isSavingCv = false;
        this.isEditingCv = false;
      },
      error: (err) => {
        this.previewError = err?.error?.detail || "Could not save CV changes.";
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

    const structured = this.structuredCv || {};
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
      })
      .subscribe({
        next: (response) => {
          const fallbackName = this.getExportFileName(this.selectedExportFormat);
          const headerName = this.extractFileName(response.headers.get("content-disposition"));
          const name = headerName || fallbackName;
          const blob = response.body;
          if (!blob) {
            this.chatError = "Generated file was empty.";
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
          this.chatError = err?.error?.detail || "CV generation failed.";
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
      this.audioNotice = "Recording...";
    } catch {
      this.cleanupMicRecording();
      this.audioNotice = "Microphone could not start. Check browser permission and device.";
    }
  }

  private stopMicRecording(): void {
    if (!this.mediaRecorder) {
      return;
    }

    this.isRecording = false;
    this.isBusy = true;
    this.isTranscribingAudio = true;
    this.audioNotice = "Transcribing your answer...";

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
      this.audioNotice = "No speech was captured. Please try again.";
      this.isBusy = false;
      this.isTranscribingAudio = false;
      return;
    }

    const audioFile = new File([audioBlob], `speech.${extension}`, { type: mimeType });

    this.api.transcribeAudio(audioFile).subscribe({
      next: (res) => {
        this.latestTranscript = (res.transcript || "").trim();
        if (this.latestTranscript) {
          this.composerText = [this.baseComposerText, this.latestTranscript]
            .filter((part) => !!part)
            .join(" ")
            .trim();
          this.audioNotice = "Transcript added to the message box.";
        } else {
          this.audioNotice = "No clear speech was detected. Please try again.";
        }
        this.isBusy = false;
        this.isTranscribingAudio = false;
      },
      error: (err) => {
        this.audioNotice = err?.error?.detail || "Audio transcription failed.";
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
