# Como contribuir — IPAJ Gaming

Guia de trabalho da dupla **Iran Pablo** e **Aloisio Junior**.

## 1. Preparar o ambiente

Siga a seção *Instalação* do [README](README.md). Resumo:

```bash
# Windows
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
# Linux/macOS
bash scripts/setup.sh
```

## 2. Fluxo de branches

- `main` é a versão estável e é publicada automaticamente (Netlify + Render).
- Cada tarefa ganha uma branch a partir da `main`:

| Prefixo | Uso | Exemplo |
|---|---|---|
| `feat/` | nova funcionalidade | `feat/laboratorio-filtros` |
| `fix/` | correção | `fix/checkout-total` |
| `docs/` | documentação | `docs/relatorio-metricas` |
| `test/` | testes | `test/regras-apriori` |
| `chore/` | infraestrutura e configs | `chore/ci-cache` |

```bash
git switch main && git pull
git switch -c feat/minha-tarefa
# ... commits ...
git push -u origin feat/minha-tarefa
```

Abra um Pull Request para `main` usando o template.

## 3. Convenção de commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/pt-br/) em português, sem acentos no resumo:

```
<tipo>: <resumo no imperativo, minusculo>
```

Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`.

Exemplos: `feat: implementar treinamento Apriori`, `fix: corrigir comportamento das recomendacoes`,
`docs: documentar metodologia e metricas`.

Cada integrante deve commitar com o próprio usuário do GitHub (`git config user.name` / `user.email`
na máquina de cada um) para que as contribuições fiquem identificáveis.

## 4. Revisão de código

1. O autor abre o PR, preenche o template e confirma que a CI passou.
2. O outro integrante revisa: lógica, testes, ausência de segredos e coerência da documentação.
3. Comentários são resolvidos com novos commits (sem `push --force` em branches compartilhadas).
4. Merge com **Squash and merge** quando aprovado; a branch é apagada em seguida.

Recomendado em *Settings → Branches*: proteger `main` exigindo PR, 1 aprovação e CI verde.

## 5. Antes de abrir o PR

```bash
# Backend
cd backend && ruff check app tests ../ml ../database ../scripts && pytest -q
# Frontend
cd frontend && npm run typecheck && npm run lint && npm test && npm run build
# Estrutura e segredos
python scripts/verify_project.py
```

Se `ml/` ou `data/` mudarem, rode o pipeline completo e **atualize as métricas** no README,
em `docs/evaluation.md` e em `docs/academic-report.md`. Nunca edite métricas à mão.

## 6. Regras de segurança

- Nunca versionar `.env`, senhas, tokens ou strings de conexão reais.
- Variáveis `VITE_*` são públicas (vão para o bundle): nada sensível nelas.
- Segredos de produção ficam apenas nos painéis do Netlify, do Render e do Supabase.
