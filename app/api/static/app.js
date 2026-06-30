const state = {
  task: null,
  latestStep: null,
  selectedStep: null,
  latestReportMarkdown: "",
  latestReportPath: "",
  websocket: null,
};

const elements = {
  topicInput: document.querySelector("#topicInput"),
  taskIdInput: document.querySelector("#taskIdInput"),
  answerInput: document.querySelector("#answerInput"),
  followUpAnswerInput: document.querySelector("#followUpAnswerInput"),
  documentFileInput: document.querySelector("#documentFileInput"),
  streamMessageInput: document.querySelector("#streamMessageInput"),
  connectionStatus: document.querySelector("#connectionStatus"),
  websocketStatus: document.querySelector("#websocketStatus"),
  taskSummary: document.querySelector("#taskSummary"),
  taskStatus: document.querySelector("#taskStatus"),
  currentStepType: document.querySelector("#currentStepType"),
  stepCount: document.querySelector("#stepCount"),
  updatedAt: document.querySelector("#updatedAt"),
  stepList: document.querySelector("#stepList"),
  currentOutput: document.querySelector("#currentOutput"),
  stepDetailOutput: document.querySelector("#stepDetailOutput"),
  selectedStepLabel: document.querySelector("#selectedStepLabel"),
  toolCallCount: document.querySelector("#toolCallCount"),
  successfulToolCallCount: document.querySelector("#successfulToolCallCount"),
  totalTokens: document.querySelector("#totalTokens"),
  totalCost: document.querySelector("#totalCost"),
  logOutput: document.querySelector("#logOutput"),
  lastAction: document.querySelector("#lastAction"),
  streamStatus: document.querySelector("#streamStatus"),
  streamOutput: document.querySelector("#streamOutput"),
  startStepButton: document.querySelector("#startStepButton"),
  executeStepButton: document.querySelector("#executeStepButton"),
  analysisButton: document.querySelector("#analysisButton"),
  reportButton: document.querySelector("#reportButton"),
  submitAnswerButton: document.querySelector("#submitAnswerButton"),
  submitFollowUpAnswerButton: document.querySelector("#submitFollowUpAnswerButton"),
  connectWebSocketButton: document.querySelector("#connectWebSocketButton"),
  downloadReportButton: document.querySelector("#downloadReportButton"),
};

function setStatus(message, isError = false) {
  elements.connectionStatus.textContent = message;
  elements.connectionStatus.classList.toggle("error", isError);
}

function writeLog(title, payload) {
  elements.lastAction.textContent = title;
  elements.logOutput.textContent =
    typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
}

function writeStream(title, payload) {
  elements.streamStatus.textContent = title;
  elements.streamOutput.textContent =
    typeof payload === "string" ? payload : JSON.stringify(payload, null, 2);
}

async function requestJson(path, options = {}) {
  setStatus("Loading");

  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    const detail = data.detail || response.statusText;
    throw new Error(`${response.status} ${detail}`);
  }

  setStatus("Ready");
  return data;
}

async function requestForm(path, formData) {
  setStatus("Loading");

  const response = await fetch(path, {
    method: "POST",
    body: formData,
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    const detail = data.detail || response.statusText;
    throw new Error(`${response.status} ${detail}`);
  }

  setStatus("Ready");
  return data;
}

function getCurrentStep(task) {
  if (!task || !task.current_step_id) {
    return null;
  }

  return task.steps.find((step) => step.step_id === task.current_step_id) || null;
}

function updateTaskView(task, step = null) {
  state.task = task;
  state.latestStep = step || getCurrentStep(task);
  state.selectedStep = state.latestStep;

  elements.taskIdInput.value = task?.task_id || "";
  elements.taskSummary.textContent = task ? `${task.topic} / ${task.task_id}` : "未创建任务";
  elements.taskStatus.textContent = task?.status || "-";
  elements.currentStepType.textContent = state.latestStep?.step_type || "-";
  elements.stepCount.textContent = String(task?.steps?.length || 0);
  elements.updatedAt.textContent = task?.updated_at || "-";

  elements.stepList.innerHTML = "";
  for (const item of task?.steps || []) {
    const stepIndex = task.steps.indexOf(item) + 1;
    const li = document.createElement("li");
    li.className = item.status;
    li.dataset.stepId = item.step_id;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "step-button";
    button.textContent = `${stepIndex}. ${item.step_type} / ${item.status}`;
    button.addEventListener("click", () => selectStep(item));

    li.appendChild(button);
    elements.stepList.appendChild(li);
  }

  const output = state.latestStep?.output || {};
  elements.currentOutput.textContent = JSON.stringify(output, null, 2);
  renderSelectedStep();
  updateActionButtons();
}

function selectStep(step) {
  state.selectedStep = step;
  renderSelectedStep();
}

function renderSelectedStep() {
  const step = state.selectedStep;
  elements.selectedStepLabel.textContent = step
    ? `${step.step_type} / ${step.status}`
    : "未选择步骤";
  elements.stepDetailOutput.textContent = JSON.stringify(step || {}, null, 2);
}

function updateActionButtons() {
  const task = state.task;
  const currentStep = getCurrentStep(task);
  const stepType = currentStep?.step_type || "";
  const hasTask = Boolean(task?.task_id);

  elements.startStepButton.disabled = !hasTask || task?.status === "completed";
  elements.executeStepButton.disabled =
    !hasTask ||
    !currentStep ||
    currentStep.status !== "running" ||
    stepType.startsWith("wait_for");
  elements.submitAnswerButton.disabled =
    !hasTask ||
    !currentStep ||
    currentStep.status !== "running" ||
    stepType !== "wait_for_answer";
  elements.submitFollowUpAnswerButton.disabled =
    !hasTask ||
    !currentStep ||
    currentStep.status !== "running" ||
    stepType !== "wait_for_follow_up_answer";
  elements.analysisButton.disabled = !hasTask;
  elements.reportButton.disabled = !hasTask;
  elements.connectWebSocketButton.disabled = !hasTask;
}

function renderTraceMetrics(analysis) {
  elements.toolCallCount.textContent = String(analysis?.tool_calls ?? "-");
  elements.successfulToolCallCount.textContent = String(
    analysis?.successful_tool_calls ?? "-"
  );
  elements.totalTokens.textContent = String(analysis?.total_tokens ?? "-");
  elements.totalCost.textContent =
    analysis?.total_cost === undefined
      ? "-"
      : `${analysis.total_cost} ${analysis.currency || ""}`.trim();
}

async function createTask() {
  const topic = elements.topicInput.value.trim();
  if (!topic) {
    throw new Error("训练方向不能为空");
  }

  const data = await requestJson("/tasks", {
    method: "POST",
    body: JSON.stringify({ topic }),
  });
  updateTaskView(data.task);
  writeLog("任务已创建", data);
}

async function loadTask() {
  const taskId = elements.taskIdInput.value.trim();
  if (!taskId) {
    throw new Error("任务 ID 不能为空");
  }

  const data = await requestJson(`/tasks/${taskId}`);
  updateTaskView(data.task);
  writeLog("任务已加载", data);
}

async function startStep() {
  const taskId = elements.taskIdInput.value.trim();
  const topic = elements.topicInput.value.trim();
  if (!taskId) {
    throw new Error("任务 ID 不能为空");
  }

  const data = await requestJson(`/tasks/${taskId}/steps/start`, {
    method: "POST",
    body: JSON.stringify({
      input: topic ? { topic } : {},
    }),
  });
  updateTaskView(data.task, data.step);
  writeLog("步骤已开始", data);
}

async function executeStep() {
  const taskId = elements.taskIdInput.value.trim();
  if (!taskId) {
    throw new Error("任务 ID 不能为空");
  }

  const data = await requestJson(`/tasks/${taskId}/steps/execute`, {
    method: "POST",
  });
  updateTaskView(data.task, data.step);
  writeLog("步骤已执行", data);
}

async function submitAnswer() {
  const taskId = elements.taskIdInput.value.trim();
  const answer = elements.answerInput.value.trim();
  if (!taskId) {
    throw new Error("任务 ID 不能为空");
  }
  if (!answer) {
    throw new Error("学生回答不能为空");
  }

  const data = await requestJson(`/tasks/${taskId}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });
  updateTaskView(data.task, data.step);
  writeLog("回答已提交", data);
}

async function submitFollowUpAnswer() {
  const taskId = elements.taskIdInput.value.trim();
  const answer = elements.followUpAnswerInput.value.trim();
  if (!taskId) {
    throw new Error("任务 ID 不能为空");
  }
  if (!answer) {
    throw new Error("追问回答不能为空");
  }

  const data = await requestJson(`/tasks/${taskId}/follow-up-answer`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });
  updateTaskView(data.task, data.step);
  writeLog("追问回答已提交", data);
}

async function showAnalysis() {
  const taskId = elements.taskIdInput.value.trim();
  if (!taskId) {
    throw new Error("任务 ID 不能为空");
  }

  const data = await requestJson(`/tasks/${taskId}/analysis`);
  renderTraceMetrics(data.analysis);
  writeLog("Trace 汇总", data.analysis);
}

async function exportReport() {
  const taskId = elements.taskIdInput.value.trim();
  if (!taskId) {
    throw new Error("任务 ID 不能为空");
  }

  const data = await requestJson(`/tasks/${taskId}/report/export`, {
    method: "POST",
  });
  state.latestReportMarkdown = data.markdown;
  state.latestReportPath = data.path;
  elements.downloadReportButton.disabled = false;
  writeLog(`报告已导出：${data.path}`, data.markdown);
}

async function uploadDocument() {
  const file = elements.documentFileInput.files[0];
  if (!file) {
    throw new Error("请选择要上传的文档");
  }

  const formData = new FormData();
  formData.append("file", file);

  const data = await requestForm("/documents/upload", formData);
  writeLog("文档已上传", data);
}

async function streamEcho() {
  const message = elements.streamMessageInput.value.trim();
  if (!message) {
    throw new Error("流式消息不能为空");
  }

  writeStream("Streaming", "");

  const url = `/stream/echo?message=${encodeURIComponent(message)}&chunk_size=8`;
  const eventSource = new EventSource(url);
  const chunks = [];

  eventSource.addEventListener("chunk", (event) => {
    const data = JSON.parse(event.data);
    chunks.push(data.text);
    writeStream("Streaming", chunks.join(""));
  });

  eventSource.addEventListener("done", (event) => {
    const data = JSON.parse(event.data);
    eventSource.close();
    writeStream(`Done / ${data.chunk_count} chunks`, chunks.join(""));
  });

  eventSource.addEventListener("error", () => {
    eventSource.close();
    setStatus("Error", true);
    writeStream("Stream Error", "SSE 连接失败");
  });
}

function connectWebSocket() {
  const taskId = elements.taskIdInput.value.trim();
  if (!taskId) {
    throw new Error("任务 ID 不能为空");
  }

  if (state.websocket) {
    state.websocket.close();
    state.websocket = null;
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const url = `${protocol}://${window.location.host}/ws/tasks/${taskId}`;
  const socket = new WebSocket(url);
  state.websocket = socket;
  elements.websocketStatus.textContent = "WS Connecting";
  elements.websocketStatus.classList.remove("error");

  socket.addEventListener("open", () => {
    elements.websocketStatus.textContent = "WS Connected";
    socket.send(JSON.stringify({ type: "ping" }));
  });

  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    writeStream(`WebSocket: ${data.type}`, data);
    if (data.task) {
      updateTaskView(data.task, data.step);
    }
  });

  socket.addEventListener("close", () => {
    elements.websocketStatus.textContent = "WS Closed";
  });

  socket.addEventListener("error", () => {
    elements.websocketStatus.textContent = "WS Error";
    elements.websocketStatus.classList.add("error");
  });
}

function downloadReport() {
  if (!state.latestReportMarkdown) {
    throw new Error("请先导出报告");
  }

  const blob = new Blob([state.latestReportMarkdown], {
    type: "text/markdown;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  const fallbackName = "task-report.md";
  const pathName = state.latestReportPath.split(/[\\/]/).pop() || fallbackName;

  link.href = url;
  link.download = pathName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function bindAction(selector, handler) {
  document.querySelector(selector).addEventListener("click", async () => {
    try {
      await handler();
    } catch (error) {
      setStatus("Error", true);
      writeLog("操作失败", error.message);
    }
  });
}

bindAction("#createTaskButton", createTask);
bindAction("#loadTaskButton", loadTask);
bindAction("#startStepButton", startStep);
bindAction("#executeStepButton", executeStep);
bindAction("#submitAnswerButton", submitAnswer);
bindAction("#submitFollowUpAnswerButton", submitFollowUpAnswer);
bindAction("#analysisButton", showAnalysis);
bindAction("#reportButton", exportReport);
bindAction("#uploadDocumentButton", uploadDocument);
bindAction("#streamEchoButton", streamEcho);
bindAction("#connectWebSocketButton", connectWebSocket);
bindAction("#downloadReportButton", downloadReport);

updateActionButtons();
