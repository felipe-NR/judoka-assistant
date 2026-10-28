"""Custo por pergunta na OpenAI a partir dos logs da API, e as gravações do prefixo que vieram
antes do TTL do cache.

Lê a saída do `journalctl -o short-iso` do serviço pela entrada padrão. Uma resposta é fria
quando grava mais da metade da entrada no cache, ou seja, quando regrava o prefixo. Uma
gravação fria antes do TTL só é esperada depois de um reinício que mude o prefixo; o
relatório mostra se a API reiniciou entre as duas perguntas.

Uso:
    ssh <usuário>@<vm> 'sudo journalctl -u judoka-api -o short-iso' \\
        | uv run python scripts/custo_openai.py [--ttl-horas 12]
"""

import argparse
import re
import statistics
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

# gpt-6-luna, prompts de até 272 mil tokens, US$ por milhão de tokens. Conferido em 2026-10-28
# em https://developers.openai.com/api/docs/pricing. A Decisions API cobra só a entrada.
_INPUT, _CACHE_READ, _CACHE_WRITE_12H, _OUTPUT = 0.10, 0.01, 0.25, 0.50

_ANSWER = re.compile(r"resposta: model=\S+ status=\S+ cache_read=(\d+) cache_write=(\d+) input=(\d+) output=(\d+)")
_GUARDRAIL = re.compile(r"guardrail: model=\S+ cache_read=(\d+) input=(\d+) output=(\d+)")
_STARTUP = "configuração: provider="


@dataclass(frozen=True)
class Answer:
    at: datetime
    cache_read: int
    cache_write: int
    input: int
    output: int

    @property
    def cold(self) -> bool:
        return self.cache_write > self.input / 2

    @property
    def cost(self) -> float:
        uncached = self.input - self.cache_read - self.cache_write
        return (
            uncached * _INPUT
            + self.cache_read * _CACHE_READ
            + self.cache_write * _CACHE_WRITE_12H
            + self.output * _OUTPUT
        ) / 1e6


def _parse(lines: list[str]) -> tuple[list[Answer], list[float], list[datetime]]:
    answers: list[Answer] = []
    guardrail_costs: list[float] = []
    startups: list[datetime] = []
    for line in lines:
        stamp = line.split(" ", 1)[0]
        if match := _ANSWER.search(line):
            read, write, inp, out = (int(g) for g in match.groups())
            answers.append(Answer(datetime.fromisoformat(stamp), read, write, inp, out))
        elif match := _GUARDRAIL.search(line):
            read, inp, _ = (int(g) for g in match.groups())
            guardrail_costs.append(((inp - read) * _INPUT + read * _CACHE_READ) / 1e6)
        elif _STARTUP in line:
            startups.append(datetime.fromisoformat(stamp))
    return answers, guardrail_costs, startups


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ttl-horas", type=float, default=12.0)
    args = parser.parse_args()
    answers, guardrail_costs, startups = _parse(sys.stdin.readlines())
    if not answers:
        sys.exit("nenhuma linha 'resposta:' na entrada")

    warm = [a.cost for a in answers if not a.cold]
    cold = [a.cost for a in answers if a.cold]
    total = sum(a.cost for a in answers)
    print(f"{len(answers)} respostas de {answers[0].at:%Y-%m-%d} a {answers[-1].at:%Y-%m-%d}: US$ {total:.4f}")
    if warm:
        print(f"  quentes: {len(warm)}, mediana US$ {statistics.median(warm):.5f} ({min(warm):.5f} a {max(warm):.5f})")
    if cold:
        print(f"  frias:   {len(cold)}, mediana US$ {statistics.median(cold):.5f}, {sum(cold) / total:.0%} do total")
    if guardrail_costs:
        print(
            f"  guardrail: {len(guardrail_costs)} classificações, mediana US$ {statistics.median(guardrail_costs):.6f}"
        )
    else:
        print("  guardrail: sem linhas 'guardrail:' na entrada")

    print("\npor dia")
    by_day: dict[str, list[Answer]] = defaultdict(list)
    for a in answers:
        by_day[f"{a.at:%Y-%m-%d}"].append(a)
    for day, day_answers in sorted(by_day.items()):
        cost = sum(a.cost for a in day_answers)
        cold_count = sum(a.cold for a in day_answers)
        print(f"  {day}  {len(day_answers):3d} respostas  {cold_count} frias  US$ {cost:.4f}")

    print(f"\ngravações antes do TTL de {args.ttl_horas:g} h")
    early = 0
    for previous, current in zip(answers, answers[1:], strict=False):
        gap_h = (current.at - previous.at).total_seconds() / 3600
        if current.cold and gap_h < args.ttl_horas:
            early += 1
            restarted = any(previous.at < s < current.at for s in startups)
            note = "com reinício entre as duas" if restarted else "sem reinício"
            print(f"  {current.at:%Y-%m-%d %H:%M}  {gap_h:4.1f} h depois da anterior, {note}")
    if not early:
        print("  nenhuma")


if __name__ == "__main__":
    main()
