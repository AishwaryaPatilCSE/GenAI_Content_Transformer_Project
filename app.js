const run = document.getElementById("run");
const result = document.getElementById("result");
const status = document.getElementById("status");
const copy = document.getElementById("copy");

run.addEventListener("click", async () => {
  const selected = [...document.querySelectorAll(".outputs input:checked")].map(x => x.value);
  if (!selected.length) {
    status.textContent = "Please select at least one output type.";
    return;
  }

  const fd = new FormData();
  fd.append("source_text", document.getElementById("source").value);
  fd.append("audience", document.getElementById("audience").value);
  fd.append("tone", document.getElementById("tone").value);
  fd.append("language", document.getElementById("language").value);
  fd.append("detail", document.getElementById("detail").value);
  fd.append("objective", document.getElementById("objective").value);
  fd.append("style", document.getElementById("style").value);
  selected.forEach(x => fd.append("outputs", x));

  const file = document.getElementById("file").files[0];
  if (file) fd.append("file", file);

  run.disabled = true;
  status.textContent = "AI is analyzing the source and generating deliverables...";
  result.textContent = "";

  try {
    const r = await fetch("/api/transform", {method:"POST", body:fd});
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Request failed");
    result.textContent = data.result;
    status.textContent = "Generation completed successfully.";
  } catch (e) {
    result.textContent = "ERROR: " + e.message;
    status.textContent = "Generation failed. Check the terminal for details.";
  } finally {
    run.disabled = false;
  }
});

copy.addEventListener("click", async () => {
  await navigator.clipboard.writeText(result.textContent);
  status.textContent = "Result copied.";
});
