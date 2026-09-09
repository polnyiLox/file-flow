const $ = (id) => document.getElementById(id);
const statusNames = { UPLOADED: "В очереди", PROCESSING: "Обработка…", READY: "Готово", FAILED: "Ошибка" };
const pageSize = 12;
let page = 1;
let uploading = false;
let refreshing = false;
let signature = "";
const urls = new Map();

function notice(message, error = false) {
  $("notice").textContent = message;
  $("notice").classList.toggle("error", error);
  $("notice").hidden = !message;
}

async function api(path, options = {}) {
  const response = await fetch(`/api/v1${path}`, { ...options, signal: AbortSignal.timeout(30000) });
  if (!response.ok) {
    const messages = { 404: "Файл больше не существует.", 409: "Дождитесь завершения обработки.", 413: "Файл слишком большой.", 422: "Проверьте формат и размер файла." };
    throw new Error(messages[response.status] || "Не удалось выполнить запрос. Попробуйте ещё раз.");
  }
  return response.status === 204 ? null : response.json();
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function formatSize(size) {
  return size < 1024 * 1024 ? `${Math.max(1, Math.round(size / 1024))} КБ` : `${(size / 1024 / 1024).toFixed(1)} МБ`;
}

async function preview(file, container) {
  if (file.status !== "READY") return;
  try {
    let cached = urls.get(file.id);
    if (!cached || Date.now() - cached.saved > 45 * 60 * 1000) {
      cached = { ...(await api(`/files/${file.id}/download`)), saved: Date.now() };
      urls.set(file.id, cached);
    }
    if (!container.isConnected || !cached.thumbnail_url) return;
    const image = element("img");
    image.alt = "";
    image.loading = "lazy";
    image.src = cached.thumbnail_url;
    image.onerror = () => { container.textContent = "JPG"; urls.delete(file.id); };
    container.replaceChildren(image);
  } catch { /* A missing preview must not hide the file or its actions. */ }
}

async function download(file, thumbnail, button) {
  button.disabled = true;
  try {
    const links = await api(`/files/${file.id}/download?attachment=true`);
    const url = thumbnail ? links.thumbnail_url : links.original_url;
    if (!url) throw new Error("Превью ещё не готово.");
    const link = element("a");
    link.href = url;
    document.body.append(link);
    link.click();
    link.remove();
  } catch (error) { notice(error.message, true); }
  finally { button.disabled = false; }
}

async function removeFile(file, button) {
  const dialog = $("delete-dialog");
  dialog.returnValue = "cancel";
  dialog.showModal();
  dialog.addEventListener("close", async () => {
    if (dialog.returnValue !== "delete") return;
    button.disabled = true;
    try {
      await api(`/files/${file.id}`, { method: "DELETE" });
      urls.delete(file.id);
      signature = "";
      notice("Изображение удалено.");
      await refresh();
    } catch (error) { notice(error.message, true); button.disabled = false; }
  }, { once: true });
}

function render(files) {
  const list = $("files");
  list.replaceChildren();
  if (!files.length) {
    const empty = element("div", "empty");
    empty.append(element("div", "empty-mark", "▧"), element("strong", "", "Пока ни одного изображения"), element("span", "", "Загрузите первый файл — он появится здесь."));
    list.append(empty);
  }
  for (const file of files) {
    const row = element("article", "file-row");
    const image = element("div", "thumbnail", file.content_type === "image/png" ? "PNG" : "JPG");
    const info = element("div", "file-info");
    const date = new Date(file.created_at).toLocaleString("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
    info.append(element("h3", "file-name", file.original_name), element("p", "file-meta", `${formatSize(file.size)} · ${date}`));
    const badge = element("span", `badge ${file.status.toLowerCase()}`, statusNames[file.status] || file.status);
    const actions = element("div", "file-actions");
    const original = element("button", "download", "Оригинал ↓");
    original.type = "button";
    original.addEventListener("click", () => download(file, false, original));
    actions.append(original);
    if (file.status === "READY") {
      const thumbnail = element("button", "download", "Превью ↓");
      thumbnail.type = "button";
      thumbnail.addEventListener("click", () => download(file, true, thumbnail));
      actions.append(thumbnail);
    }
    const remove = element("button", "delete", "×");
    remove.type = "button";
    remove.setAttribute("aria-label", `Удалить ${file.original_name}`);
    remove.disabled = ["UPLOADED", "PROCESSING"].includes(file.status);
    remove.title = remove.disabled ? "Дождитесь окончания обработки" : "Удалить изображение";
    remove.addEventListener("click", () => removeFile(file, remove));
    actions.append(remove);
    row.append(image, info, badge, actions);
    list.append(row);
    preview(file, image);
  }
  $("previous").disabled = page === 1;
  $("next").disabled = files.length < pageSize;
  $("page-label").textContent = `Страница ${page}`;
}

async function refresh() {
  if (refreshing) return;
  refreshing = true;
  $("refresh").disabled = true;
  try {
    let files = await api(`/files?page=${page}&page_size=${pageSize}`);
    if (!files.length && page > 1) {
      page -= 1;
      files = await api(`/files?page=${page}&page_size=${pageSize}`);
    }
    const nextSignature = `${page}:${JSON.stringify(files)}`;
    if (signature !== nextSignature) { render(files); signature = nextSignature; }
    try {
      const stats = await api("/analytics/overview");
      $("uploaded-count").textContent = stats.files_uploaded;
      $("processed-count").textContent = stats.files_processed;
      $("failed-count").textContent = stats.files_failed;
    } catch {
      for (const id of ["uploaded-count", "processed-count", "failed-count"]) $(id).textContent = "—";
    }
  } catch (error) {
    notice("Не удалось обновить список. Проверьте соединение и нажмите «Обновить».", true);
    if (!signature) $("files").replaceChildren(element("div", "empty", "Список изображений временно недоступен."));
  } finally {
    refreshing = false;
    $("refresh").disabled = false;
    $("files").setAttribute("aria-busy", "false");
  }
}

async function upload(file) {
  if (!file || uploading) return;
  if (!["image/png", "image/jpeg"].includes(file.type) || !/\.(png|jpe?g)$/i.test(file.name)) return notice("Выберите изображение PNG или JPG.", true);
  if (!file.size || file.size > 10 * 1024 * 1024) return notice("Размер файла должен быть от 1 байта до 10 МБ.", true);
  uploading = true;
  $("choose-file").disabled = true;
  $("choose-file").textContent = "Загружаем…";
  notice("");
  const body = new FormData();
  body.append("file", file);
  try {
    await api("/files", { method: "POST", body });
    page = 1;
    signature = "";
    notice("Изображение загружено. Статус обработки обновится автоматически.");
    await refresh();
  } catch (error) { notice(`${error.message} Если загрузка прервалась, сначала обновите список перед повторной попыткой.`, true); }
  finally {
    uploading = false;
    $("choose-file").disabled = false;
    $("choose-file").textContent = "Выбрать изображение ＋";
    $("file-input").value = "";
  }
}

$("choose-file").addEventListener("click", () => $("file-input").click());
$("file-input").addEventListener("change", (event) => upload(event.target.files[0]));
$("refresh").addEventListener("click", () => { notice(""); signature = ""; refresh(); });
$("previous").addEventListener("click", () => { if (!refreshing && page > 1) { page -= 1; refresh(); } });
$("next").addEventListener("click", () => { if (!refreshing) { page += 1; refresh(); } });
$("drop-zone").addEventListener("dragover", (event) => { event.preventDefault(); $("drop-zone").classList.add("dragging"); });
$("drop-zone").addEventListener("dragleave", () => $("drop-zone").classList.remove("dragging"));
$("drop-zone").addEventListener("drop", (event) => {
  event.preventDefault();
  $("drop-zone").classList.remove("dragging");
  if (event.dataTransfer.files.length !== 1) return notice("Загружайте по одному изображению.", true);
  upload(event.dataTransfer.files[0]);
});
refresh();
setInterval(() => { if (!document.hidden && !$("delete-dialog").open) refresh(); }, 4000);
