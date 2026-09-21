document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const savedTheme = localStorage.getItem("probstat-theme");
  if (savedTheme === "dark") body.classList.add("dark-mode");

  document.querySelectorAll("#themeToggle").forEach((button) => {
    button.addEventListener("click", () => {
      body.classList.toggle("dark-mode");
      localStorage.setItem("probstat-theme", body.classList.contains("dark-mode") ? "dark" : "light");
    });
  });

  const search = document.getElementById("datasetSearch");
  if (search) {
    search.addEventListener("input", () => {
      const term = search.value.toLowerCase();
      document.querySelectorAll(".dataset-preview tbody tr").forEach((row) => {
        row.style.display = row.innerText.toLowerCase().includes(term) ? "" : "none";
      });
    });
  }

  const operation = document.getElementById("operationSelect");
  if (operation) {
    const syncFields = () => {
      const between = operation.value === "between";
      document.querySelectorAll(".single-bound").forEach((el) => el.classList.toggle("d-none", between));
      document.querySelectorAll(".between-bound").forEach((el) => el.classList.toggle("d-none", !between));
    };
    operation.addEventListener("change", syncFields);
    syncFields();
  }

  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((element) => {
    new bootstrap.Tooltip(element);
  });

  const probabilityForm = document.getElementById("probabilityForm");
  if (probabilityForm) {
    const submitButton = document.getElementById("probabilitySubmit");
    const spinner = document.getElementById("probabilitySpinner");
    const errorBox = document.getElementById("probabilityError");
    const resultBox = document.getElementById("probabilityResult");
    const formulaBox = document.getElementById("probabilityFormula");
    const interpretationBox = document.getElementById("probabilityInterpretation");
    const stepsBox = document.getElementById("probabilitySteps");
    const explanationProbabilityBody = document.getElementById("explanationProbabilityBody");

    const setLoading = (loading) => {
      submitButton.disabled = loading;
      spinner.classList.toggle("d-none", !loading);
      submitButton.querySelector(".submit-label").textContent = loading ? "Calculating" : "Calculate";
    };

    const renderSteps = (steps) => steps.map((step) => `
      <div class="step-row">
        <span>${step.label}</span>
        <strong>\\(${step.math}\\)</strong>
      </div>
    `).join("");

    const typesetMath = () => {
      if (window.MathJax?.typesetPromise) {
        window.MathJax.typesetPromise();
      }
    };

    probabilityForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.classList.add("d-none");
      resultBox.classList.remove("show");
      setLoading(true);

      const formData = new FormData(probabilityForm);
      const payload = {
        operation: formData.get("operation"),
        x_value: formData.get("x_value"),
        a_value: formData.get("a_value"),
        b_value: formData.get("b_value"),
      };

      try {
        const response = await fetch(probabilityForm.action, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
          throw new Error(data.error || "Probability calculation failed.");
        }

        formulaBox.innerHTML = `\\(${data.result_math}\\)`;
        interpretationBox.textContent = data.interpretation;
        stepsBox.innerHTML = renderSteps(data.step_items);
        if (explanationProbabilityBody) {
          explanationProbabilityBody.innerHTML = `<div class="probability-steps">${renderSteps(data.step_items)}</div>`;
        }
        resultBox.classList.remove("d-none");
        requestAnimationFrame(() => resultBox.classList.add("show"));
        typesetMath();
      } catch (error) {
        errorBox.textContent = error.message;
        errorBox.classList.remove("d-none");
      } finally {
        setLoading(false);
      }
    });
  }
});
