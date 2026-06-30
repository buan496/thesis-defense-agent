const state = {
  task: null,
  latestStep: null,
};

const elements = {
  topicInput: document.querySelector("#topicInput"),
  taskIdInput: document.querySelector("#taskIdInput"),
  answerInput: document.querySelector("#answerInput"),
  followUpAnswerInput: document.querySelector("#followUpAnswerInput"),
  connectionStatus: document.querySelector("#connectionStatus"),
  taskSummary: document.querySelector("#taskSummary"),
  taskStatus: document.querySelector("#taskStatus"),
  currentStepType: document.querySelector("#currentStepType"),
  stepCount: document.querySelector("#stepCount"),
  updatedAt: document.querySelector("#updatedAt"),
  stepList: document.querySelector("#stepList"),
  currentOutput: document.querySelector("#currentOutput"),
  logOutput: document.querySelector("#logOutput"),
  lastAction: document.querySelector("#lastAction"),
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

function getCurrentStep(task) {
  if (!task || !task.current_step_id) {
    return null;
  }

  return task.steps.find((step) => step.step_id === task.current_step_id) || null;
}

function updateTaskView(task, step = null) {
  state.task = task;
  state.latestStep = step || getCurrentStep(task);

  elements.taskIdInput.value = task?.task_id || "";
  elements.taskSummary.textContent = task ? `${task.topic} / ${task.task_id}` : "未创建任务";
  elements.taskStatus.textContent = task?.status || "-";
  elements.currentStepType.textContent = state.latestStep?.step_type || "-";
  elements.stepCount.textContent = String(task?.steps?.length || 0);
  elements.updatedAt.textContent = task?.updated_at || "-";

  elements.stepList.innerHTML = "";
  for (const item of task?.steps || []) {
    const li = document.createElement("li");
    li.className = item.status;
    li.textContent = `${item.step_type} / ${item.status}`;
    elements.stepList.appendChild(li);
  }

  const output = state.latestStep?.output || {};
  elements.currentOutput.textContent = JSON.stringify(output, null, 2);
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
  writeLog(`报告已导出：${data.path}`, data.markdown);
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
