# ofrenda

A small offline command-line tool that helps you remember someone.

You answer a few quiet questions about a person — what they cooked, a song they hummed, a phrase they always said — and the tool writes two plain Markdown files: a short remembrance and a checklist of things you might put on an ofrenda. Everything runs on a local model through Ollama, so nothing leaves your machine.

I made this during Hacktoberfest 2026, Week 4: Ghost in the Machine. The theme was about honoring the past, and Día de los Muertos felt like the right frame — a celebration of memory, not loss.

---

## Install and run

**1. Install Ollama**

Download from [ollama.com](https://ollama.com) and make sure it's running.

**2. Pull a model**

```bash
ollama pull gemma3:4b
```

Any other small model works too. You can change it in the config (see below).

**3. Install ofrenda**

```bash
git clone https://github.com/yourname/ofrenda-cli.git
cd ofrenda-cli
pip install -e .
```

**4. Run it**

```bash
ofrenda new
```

---

## Example session

```
$ ofrenda new

ofrenda
A quiet place to remember someone.

Who are you remembering: Abuela Rosa
How did you know them: my grandmother

  ──────────────────────────────────────────
  Remembering Abuela Rosa — my grandmother
  Type skip to skip a question, done to finish early.
  ──────────────────────────────────────────

What did Abuela Rosa love to cook or eat?
> She made tamales every Sunday. Pork, with a salsa she never wrote down.

That sounds like something you could smell from the street. Was there music
she was known for — a song she hummed, or something she always had playing?
> La Llorona. She sang it quietly while she worked.

"La Llorona" has a way of staying with you. Was there a phrase she used a
lot — something she said so often it became hers?
> "Mija, come and eat." Even when you weren't hungry.

A place that was hers — a room, a street, somewhere tied to her?
> Her kitchen. The whole house smelled like it.

A small habit or gesture, something almost invisible that was just her?
> She kept a rosary on the windowsill and touched it every morning.

One object you'd want on her ofrenda — something physical?
> The clay pot she used for tamales. It's still in the family.

Is there anything else you'd like to add?
> She died during the pandemic. We couldn't be with her.

Thank you for sharing this.

Writing remembrance...
Building ofrenda checklist...

Saved to ofrendas/abuela-rosa
  ofrendas/abuela-rosa/remembrance.md
  ofrendas/abuela-rosa/ofrenda.md
```

**`remembrance.md`**

```markdown
# Abuela Rosa

Abuela Rosa made tamales every Sunday — pork, with a salsa she never wrote
down. The smell reached the street. While she worked, she sang La Llorona
quietly to herself. Her kitchen was the center of the house.

She kept a rosary on the windowsill and touched it every morning. When you
walked in, she'd say "Mija, come and eat," whether you were hungry or not.
The clay pot she used for tamales is still in the family.

She died during the pandemic. The family couldn't be with her.
```

**`ofrenda.md`**

```markdown
# Ofrenda for Abuela Rosa

## Foods & drinks
- [ ] Tamales (pork, with her salsa)

## Music
- [ ] La Llorona

## Objects & keepsakes
- [ ] The clay tamale pot
- [ ] Her rosary
```

---

## Why a local model

Family stories are private. Names, dates, how someone died — none of that should go to a cloud API by default. With Ollama, the model runs on your laptop. Wi-Fi off, it still works. You can swap the model for anything Ollama supports. It costs nothing to run.

---

## Other commands

```bash
ofrenda list           # show all saved remembrances
ofrenda show rosa      # print one (use the folder name or person's name)
ofrenda new --model gemma3:1b   # use a smaller/faster model
```

**Config file** (`~/.ofrenda.toml`):

```toml
model = "gemma3:4b"
data_dir = "/home/you/ofrendas"
ollama_url = "http://localhost:11434"
```

---

## Known limitations

- The model sometimes ignores the "one question at a time" instruction and asks two at once. It's a prompt engineering problem, not a code one. You can edit `prompts/interviewer.txt` to push harder on it.
- Very short answers produce very short remembrances. The tool won't invent — if you give it little, the file will be sparse. That's a feature, not a bug.
- No streaming output. The model thinks in silence, then prints. On slow hardware this can feel like a pause.
- The interview history is sent to the model on every turn (so it can react to earlier answers). On long interviews with small context windows, earlier answers may drop out.
- `ofrenda show` matches on slug (lowercased, spaces → dashes). If the match fails, try the exact folder name under `ofrendas/`.

---

## Project notes

Started and completed during [Hacktoberfest 2026](https://hacktoberfest.com) Week 4 (October 2026).

`prompts/` contains the plain-text system prompts. They're the most important part of the tool — read them before you trust anything the model writes.

---

## License

MIT. See `LICENSE`.
