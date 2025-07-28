from datetime import datetime

class CollectionReport:
    """
    Acumula os resultados da coleta e gera um relatório de execução.
    """
    def __init__(self):
        self.start_time = datetime.now()
        self.successes = []
        self.failures = []

    def add_success(self, metric, source, destination, filepath):
        """Registra uma coleta bem-sucedida."""
        self.successes.append({
            "metric": metric,
            "source": source,
            "destination": destination,
            "filepath": filepath
        })

    def add_failure(self, metric, source, destination, reason):
        """Registra uma falha na coleta."""
        self.failures.append({
            "metric": metric,
            "source": source,
            "destination": destination,
            "reason": reason
        })

    def generate_report_text(self):
        """Monta o texto completo do relatório."""
        end_time = datetime.now()
        duration = end_time - self.start_time
        total_attempts = len(self.successes) + len(self.failures)

        report_lines = []
        report_lines.append("======================================================")
        report_lines.append("=          RELATÓRIO DE EXECUÇÃO DA COLETA         =")
        report_lines.append("======================================================")
        report_lines.append(f"Início da Execução: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Fim da Execução:    {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Duração Total:      {str(duration).split('.')[0]}")
        report_lines.append("")

        # --- Sumário ---
        report_lines.append("--- SUMÁRIO ---")
        report_lines.append(f"Total de Tentativas de Coleta: {total_attempts}")
        report_lines.append(f"  - Sucessos: {len(self.successes)}")
        report_lines.append(f"  - Falhas:   {len(self.failures)}")
        if total_attempts > 0:
            success_rate = (len(self.successes) / total_attempts) * 100
            report_lines.append(f"Taxa de Sucesso: {success_rate:.2f}%")
        report_lines.append("")

        # --- Detalhes das Falhas (O que falta) ---
        report_lines.append("--- DETALHES DAS FALHAS ---")
        if not self.failures:
            report_lines.append("Nenhuma falha registrada. Todas as coletas foram bem-sucedidas!")
        else:
            for fail in self.failures:
                report_lines.append(
                    f"- Métrica: {fail['metric']}, "
                    f"Par: {fail['source']} -> {fail['destination']}"
                )
                report_lines.append(f"  Motivo: {fail['reason']}")
        report_lines.append("")
        
        # --- Detalhes dos Sucessos (O que tem) ---
        report_lines.append("--- DETALHES DOS SUCESSOS ---")
        if not self.successes:
            report_lines.append("Nenhum sucesso registrado.")
        else:
            report_lines.append(f"{len(self.successes)} arquivos salvos com sucesso na pasta data/raw/")
            # Descomente as linhas abaixo se quiser uma lista detalhada de cada sucesso
            # for success in self.successes:
            #     report_lines.append(f"- {success['filepath']}")

        report_lines.append("\n======================================================")
        
        return "\n".join(report_lines)

    def save_report(self, output_dir):
        """Gera e salva o relatório em um arquivo .txt."""
        report_text = self.generate_report_text()
        filename = f"relatorio_coleta_{self.start_time.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        filepath = f"{output_dir}/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n[INFO] Relatório de execução salvo em: {filepath}")
        except Exception as e:
            print(f"\n[ERRO] Não foi possível salvar o relatório: {e}")