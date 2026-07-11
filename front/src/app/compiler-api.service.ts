import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';

import { AnalyzeRequest, AnalyzeResponse, ModelsResponse } from './compiler-api.types';

@Injectable({ providedIn: 'root' })
export class CompilerApiService {
  private readonly baseUrl = 'http://localhost:8000';

  constructor(private readonly http: HttpClient) {}

  analyze(payload: AnalyzeRequest) {
    return this.http.post<AnalyzeResponse>(`${this.baseUrl}/compiler/analyze`, payload);
  }

  getModels() {
    return this.http.get<ModelsResponse>(`${this.baseUrl}/compiler/models`);
  }
}
