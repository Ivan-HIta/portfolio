/*
 * Este módulo define la estructura de cada caso de estudio que se mostrará en
 * páginas dinámicas. Cada proyecto incluye un slug para la ruta, un título
 * corto, un resumen para tarjetas y secciones de contexto, acciones
 * realizadas, resultados y la pila tecnológica utilizada. Puedes ampliar
 * la información o añadir métricas adicionales según sea necesario.
 * El catálogo reúne proyectos de ML, AI, Data y riesgo con enfoque reproducible.
 * Actualizado con nuevos casos de estudio de operaciones, riesgo y gobernanza de IA.
 */

export interface Project {
  slug: string;
  title: string;
  summary: string;
  context: string;
  actions: string[];
  results: string[];
  stack: string[];
}

export const projects: Project[] = [
  {
    slug: "modelo-riesgo-nomina",
    title: "Modelo de Riesgo de Préstamos de Nómina",
    summary:
      "Rediseño del scorecard de nómina con regresión logística y Elastic Net para aumentar aprobaciones y reducir morosidad.",
    context:
      "Los modelos tradicionales perdían poder predictivo en nuevas generaciones de clientes. Se requería discriminar mejor entre solicitantes de bajo y alto riesgo y adaptarse a la infraestructura de Big Data (Hadoop + PySpark).",
    actions: [
      "Definición de población objetivo y ventana de observación (36 meses con horizonte de 12 meses).",
      "Análisis de vintages para detectar deterioro en segmentos (empleadores pequeños vs. grandes).",
      "Implementación de Reject Inference mediante parceling y reweighting para incluir solicitantes rechazados.",
      "Ingeniería de más de 800 variables a partir de historial de buró, transacciones de nómina y comportamiento digital usando Featuretools, TSFresh y PySpark MLlib; selección mediante Information Value y PSI.",
      "Entrenamiento de regresión logística con Elastic Net, optimizando hiperparámetros mediante Algoritmos Genéticos (DEAP).",
      "Validación cruzada, backtesting por cohorte y despliegue en pipelines de PySpark; creación de tableros de monitoreo en Tableau."
    ],
    results: [
      "Mejora del estadístico KS en +12 puntos frente al scorecard previo.",
      "Reducción de morosidad temprana en un 10% en las últimas generaciones.",
      "Aumento de aprobaciones en un 9% manteniendo el riesgo controlado.",
      "Modelo interpretable y estable que facilitó la aprobación regulatoria y se replicó en otros productos."
    ],
    stack: ["PySpark", "Hadoop", "Python", "Elastic Net", "Genetic Algorithms", "Tableau"]
  },
  {
    slug: "modelo-prestamo-personal-xgboost",
    title: "Modelo de Riesgo de Préstamos Personales",
    summary:
      "Modelo XGBoost con optimización bayesiana para incrementar aprobaciones y capturar relaciones no lineales.",
    context:
      "La cartera de préstamos personales mostraba aumento de morosidad y los scorecards tradicionales carecían de flexibilidad. Se buscaba un modelo más potente y escalable en la nube.",
    actions: [
      "Definición de población objetivo y ventana de 24 meses con outcome de 12 meses.",
      "Análisis de vintages para evidenciar deterioro en cohorts recientes.",
      "Aplicación de Reject Inference (parceling y reweighting) para incluir solicitantes rechazados.",
      "Ingeniería de más de 500 características (buró, transacciones internas, señal digital) y selección por valor de información y GINI marginal.",
      "Entrenamiento de XGBoost con optimización bayesiana de hiperparámetros (max_depth, eta, subsample, colsample).",
      "Validación cruzada y pruebas out‑of‑time por segmento; despliegue del modelo en AWS Sagemaker con monitoreo de PSI y KS."
    ],
    results: [
      "Incremento del KS en +10 puntos respecto al modelo logístico heredado.",
      "Aumento de aprobaciones en 12% con reducción de morosidad temprana en 8%.",
      "Permite aprovechar datos alternativos y se convirtió en el modelo campeón para originación de préstamos personales."
    ],
    stack: ["XGBoost", "Bayesian Optimization", "Python", "PySpark", "AWS Sagemaker", "SHAP"]
  },
  {
    slug: "modelo-nomina-no-hit-mlp",
    title: "Modelo Nómina para Clientes Sin Historial (No‑Hit)",
    summary:
      "MLP con Matching y Algoritmos Genéticos para segmentar y aprobar a clientes sin buró crediticio.",
    context:
      "El banco buscaba aumentar la penetración en jóvenes y recién bancarizados sin historial crediticio. El scorecard tradicional rechazaba a la mayoría y mostraba morosidad temprana.",
    actions: [
      "Selección de aplicaciones de nómina sin buró en 30 meses con ventana de 12 meses para defaults.",
      "Construcción de curvas de vintages en PySpark para detectar deterioro acelerado en segmentos pequeños.",
      "Implementación de Reject Inference mediante Propensity Score Matching para emparejar rechazados con aprobados de perfiles similares.",
      "Ingeniería de más de 1 000 variables (variabilidad de ingresos de nómina, comportamiento digital, demográficos) y reducción a ~200 por IV y PSI.",
      "Diseño y entrenamiento de una red neuronal MLP con tres capas ocultas (128→64→32) y activaciones ReLU, con regularización por Dropout y focal loss para desbalance.",
      "Optimización de hiperparámetros mediante Algoritmo Genético (número de capas, learning rate, dropout) con función de fitness basada en KS.",
      "Validación cruzada, backtesting por vintages y despliegue en Hadoop + PySpark, exponiendo el modelo como API en Docker/K8s y monitoreado mediante dashboards en Tableau."
    ],
    results: [
      "Mejora del KS en +11 puntos frente al scorecard para clientes sin historial.",
      "Aumento de aprobaciones en 15% y reducción de morosidad temprana en 10%.",
      "El modelo permitió captar nuevos segmentos de jóvenes profesionales y fue reconocido como innovación en la organización."
    ],
    stack: ["PyTorch", "PySpark", "PSM", "Genetic Algorithms", "Docker", "Kubernetes"]
  },
  {
    slug: "segmentacion-primacia",
    title: "Segmentación de Clientes por Primacía",
    summary:
      "Clustering de comportamiento para entender la lealtad y maximizar campañas de marketing.",
    context:
      "El banco necesitaba identificar qué clientes consideran al banco su principal proveedor financiero para enfocar estrategias de retención, cross‑selling y fidelización.",
    actions: [
      "Recolección de variables demográficas, socioeconómicas, cartera de productos, actividad transaccional y engagement digital.",
      "Limpieza, imputación y escalamiento de datos; reducción de dimensionalidad mediante PCA y selección de características relevantes.",
      "Implementación de métodos de clustering (K‑means, DBSCAN) para agrupar clientes según primacía y comportamiento financiero.",
      "Análisis de perfiles resultantes: clientes digitales de alto valor, nuevos entrantes en crecimiento, tradicionalistas leales y clientes de bajo engagement.",
      "Validación del valor de negocio mediante campañas piloto y construcción de un clasificador supervisado para asignar nuevos clientes a los clústeres en tiempo real."
    ],
    results: [
      "Identificación de segmentos claros que permitieron personalizar ofertas y priorizar inversión en marketing.",
      "Aumento de conversión en campañas dirigidas (>20% en segmentos digitales) y reducción de churn.",
      "Marco de micro‑segmentación implementado para soportar decisiones estratégicas a largo plazo."
    ],
    stack: ["Python", "Scikit‑learn", "PySpark", "K‑means", "PCA", "Tableau"]
  },
  {
    slug: "analisis-sentimientos-cobranza",
    title: "Análisis de Sentimientos para Cobranza",
    summary:
      "Clasificación de sentimientos con BETO para priorizar esfuerzos de cobranza y mejorar recuperación.",
    context:
      "El área de cobranza enfrentaba aumento de morosidad y quejas por contacto intrusivo. Se necesitaba un sistema que predijera la probabilidad de pago a partir de la intención del cliente expresada en textos y llamadas.",
    actions: [
      "Recolección de grabaciones de llamadas y chats de cobranza; anonimización y limpieza de datos sensibles.",
      "Entrenamiento de un modelo BETO (BERT en español) para clasificación de sentimientos (positivo, neutro, negativo) y detección de promesas de pago.",
      "Integración con variables estructuradas (saldo pendiente, días de atraso, segmento socioeconómico) para alimentar un modelo secundario de predicción de pago.",
      "Implementación de pipeline MLOps en AWS con retraining mensual, marco champion–challenger y monitoreo de drift de vocabulario.",
      "Iteración continua: incorporación de embeddings contextuales cuando se detectó deterioro de AUC en 2025."
    ],
    results: [
      "AUC ≈ 0.90, recall 80–85 % y precision 25–30 % (frente a 0.80/60 %/10 % del sistema basado en reglas).",
      "Reducción de falsos negativos en 50 % y detección de ~40 % más pagos potenciales.",
      "Ahorro significativo en costos de cobranza y mejora de la experiencia del cliente."
    ],
    stack: ["BETO", "Transformers", "PyTorch", "AWS", "MLOps"]
  },
  {
    slug: "deteccion-fraude-llm-mlp",
    title: "Detección de Fraude en Transferencias con LLM + MLP",
    summary:
      "Modelo híbrido que combina embeddings de lenguaje y atributos tabulares para anticipar fraudes en transacciones.",
    context:
      "El banco experimentaba un incremento de fraudes en transferencias y bloqueos erróneos de cuentas. Se requería mejorar la detección temprana sin afectar la experiencia de clientes legítimos.",
    actions: [
      "Consolidación de datos transaccionales y contextuales (motivo de transferencia, descripciones) y etiquetado de casos de fraude/no fraude.",
      "Extracción de embeddings semánticos a partir de descripciones de transferencias con modelos LLM en español.",
      "Diseño de una red MLP para combinar embeddings de texto con atributos tabulares (monto, frecuencia, geolocalización, historial de usuario).",
      "Selección de características relevantes y entrenamiento del modelo híbrido con regularización y técnicas de oversampling para clases desbalanceadas.",
      "Implementación de pipelines MLOps en AWS SageMaker, con API de inferencia de baja latencia (<300 ms) y dashboards de métricas."
    ],
    results: [
      "Recall ≈ 96.2 %, precision ≈ 84.1 % y AUC ≈ 0.991, superando al modelo tabular en 1.7 puntos de recall y reduciendo falsos positivos en 15 %.",
      "Reducción de pérdidas por fraude en ~50 % (~4.5 M MXN/año) y mejora significativa en la experiencia de clientes.",
      "Capacitación del equipo y establecimiento de mejores prácticas de MLOps y compliance."
    ],
    stack: ["Transformers", "PyTorch", "MLP", "AWS", "MLOps"]
  },
{
  "slug": "ai-model-validation-governance-toolkit",
  "title": "AI Model Validation & Governance Toolkit",
  "summary": "Workbench offline para validar modelos de clasificación, evaluar respuestas LLM/RAG y convertir métricas de sesgo, estabilidad y drift en evidencia de gobernanza.",
  "context": "En entornos financieros y empresariales de alta responsabilidad, el rendimiento predictivo por sí solo no basta: también se necesita evidencia reproducible sobre calidad, estabilidad, diferencias entre segmentos, límites de uso y monitoreo. Este proyecto simula ese proceso con datos sintéticos y mantiene la revisión humana como control.",
  "actions": [
    "Generación y documentación de datasets sintéticos para un clasificador binario y pares de evaluación LLM/RAG.",
    "Entrenamiento y comparación de regresión logística y Random Forest con holdout, ROC AUC, matriz de confusión, calibración, umbrales y lift por deciles.",
    "Cálculo de recall, FPR y FNR por región, segmento, edad e ingreso para identificar patrones que requieren investigación.",
    "Implementación de indicadores de estabilidad y drift tipo PSI, además de controles transparentes de cobertura de conceptos, relevancia y posibles omisiones en respuestas LLM.",
    "Generación de model cards en Markdown, dashboard de gobernanza, checklist de aprobación y suite de pruebas offline."
  ],
  "results": [
    "Paquete trazable de evidencia de validación, sesgo, estabilidad, drift y evaluación LLM en una sola aplicación.",
    "Arquitectura modular y reproducible que separa generación de datos, entrenamiento, métricas, visualización y artefactos de gobernanza.",
    "Demostración explícita de límites, supervisión humana y controles pendientes antes de cualquier uso productivo."
  ],
  "stack": [
    "Python",
    "Streamlit",
    "scikit-learn",
    "pandas",
    "Plotly",
    "pytest",
    "Model Governance",
    "LLM Evaluation"
  ]
},
{
  "slug": "ai-operations-workflow-copilot",
  "title": "AI Operations Workflow Copilot",
  "summary": "Copiloto con NLP, reglas de negocio y revisión humana para clasificar tickets operativos, resumir incidencias y recomendar próximas acciones.",
  "context": "Los equipos de operaciones financieras reciben excepciones y solicitudes que deben priorizarse con rapidez y consistencia. El proyecto simula una asistencia explicable que mantiene la decisión final en manos de un analista y deja una trazabilidad local de sus revisiones.",
  "actions": [
    "Carga y validación de tickets sintéticos o CSV del usuario con documentación del contrato de datos.",
    "Clasificación de categorías mediante TF-IDF y regresión logística, con accuracy, precision, recall, F1, matriz de confusión y ejemplos de error.",
    "Generación de resúmenes extractivos y fallback determinista sin API, junto con recomendaciones de siguiente acción basadas en reglas transparentes.",
    "Flujo human-in-the-loop para aceptar, rechazar o ajustar la propuesta de IA y persistir comentarios y decisiones en SQLite.",
    "Dashboard de beneficios con tiempo de triage, ahorro estimado, riesgo de incumplimiento de SLA y validación del modelo."
  ],
  "results": [
    "Flujo completo de triage asistido que conecta inferencia, recomendación, revisión humana, auditoría y medición de beneficios.",
    "Separación clara entre predicción probabilística y reglas operativas controladas, facilitando revisión y pruebas.",
    "Demo local reproducible, sin credenciales ni datos confidenciales, con pruebas unitarias y documentación de limitaciones."
  ],
  "stack": [
    "Python",
    "Streamlit",
    "scikit-learn",
    "TF-IDF",
    "SQLite",
    "SQLAlchemy",
    "Plotly",
    "pytest",
    "Human-in-the-loop AI"
  ]
},
{
  "slug": "investment-operations-exception-monitor",
  "title": "Investment Operations Exception Monitor",
  "summary": "Monitor de excepciones de operaciones de inversión con validación de datos, triage determinista, routing, SLA analytics y dashboard auditable.",
  "context": "Las operaciones de inversión gestionan breaks de reconciliación, confirmaciones faltantes, diferencias de precio, incidencias contables y liquidaciones fallidas. El valor del proyecto está en convertir una lista de excepciones en un flujo controlable de calidad, prioridad, responsable y riesgo de vencimiento.",
  "actions": [
    "Validación de esquema y registros sintéticos: campos faltantes, duplicados, fechas inválidas, importes negativos y estados inesperados.",
    "Motor de reglas explicable para calcular prioridad, severidad, equipo responsable, riesgo SLA y causa raíz de respaldo.",
    "Monitoreo de fechas objetivo, excepciones vencidas, elementos en riesgo, tiempo restante y puntualidad de resolución.",
    "Dashboards de volumen, severidad, tipo de excepción, carga por equipo, exposición SLA y causas recurrentes.",
    "Carga CSV, módulos reutilizables, pruebas unitarias y documentación de controles, alcance y límites."
  ],
  "results": [
    "Flujo auditable desde la ingestión hasta el triage, routing y monitoreo de SLA.",
    "Reglas de decisión visibles y testeables que pueden ser desafiadas durante una revisión operativa.",
    "Vista de gestión orientada a priorizar excepciones de mayor impacto sin automatizar cierres ni sustituir aprobaciones."
  ],
  "stack": [
    "Python",
    "Streamlit",
    "pandas",
    "NumPy",
    "Plotly",
    "SQLAlchemy",
    "pytest",
    "Rules Engine",
    "SLA Analytics"
  ]
},
{
  "slug": "portfolio-risk-scenario-analytics",
  "title": "Portfolio Risk & Scenario Analytics",
  "summary": "Aplicación de analítica de exposición, concentración, métricas históricas de riesgo y escenarios deterministas sobre un portafolio sintético.",
  "context": "Una tabla de posiciones no basta para entender concentración, calidad de datos, comportamiento histórico ni sensibilidad ante shocks. Este proyecto construye una ruta transparente desde la validación de holdings y precios hasta la analítica de riesgo y escenarios, sin utilizar datos de mercado reales.",
  "actions": [
    "Validación de holdings y precios sintéticos: campos requeridos, missingness, precios inválidos, duplicados, valores negativos y conciliación aproximada de pesos.",
    "Cálculo de valor de mercado, exposiciones por clase de activo, sector, región y moneda, además de concentración y HHI.",
    "Construcción de retornos diarios y cálculo de volatilidad, volatilidad anualizada, drawdown máximo, VaR histórico, CVaR, Sharpe y sensibilidad tipo beta.",
    "Ejecución de escenarios explicables de equity, tasas, moneda, sector, mercados emergentes y shocks personalizados.",
    "Dashboards y reportes para comparar valor base, valor estresado, impacto por holding y grupos de exposición."
  ],
  "results": [
    "Cadena reproducible de validación, exposición, riesgo histórico y stress testing sobre datos completamente sintéticos.",
    "Métricas y supuestos documentados para facilitar la revisión técnica y de negocio.",
    "Demostración de analítica de riesgo sin ejecutar operaciones, emitir recomendaciones de inversión ni sustituir controles especializados."
  ],
  "stack": [
    "Python",
    "Streamlit",
    "pandas",
    "NumPy",
    "SciPy",
    "Plotly",
    "pytest",
    "Risk Analytics",
    "Scenario Engine"
  ]
},
  {
    slug: "data-platform-observability",
    title: "Data Platform Observability",
    summary:
      "Plataforma batch reproducible para ingestión incremental, contratos de datos, calidad, agregaciones analíticas y observabilidad operativa.",
    context:
      "Los equipos de negocio necesitan confiar en sus métricas y detectar fallas antes de que lleguen a reportes o modelos. El caso simula eventos operativos y los lleva desde una capa raw hasta agregados gold con evidencia de calidad.",
    actions: [
      "Generación de datos sintéticos con claves determinísticas y ejecución segura ante reruns.",
      "Validación de esquema, nulos, duplicados, frescura, tipos y reglas de integridad antes de publicar la capa curated.",
      "Separación bronze/silver/gold, métricas de calidad y dashboard Streamlit para operación.",
      "Documentación de mapeo a object storage, Spark/Databricks, BigQuery/Snowflake, Airflow/Dagster, Kafka, dbt, Kubernetes y Terraform.",
      "Pruebas automatizadas, Docker y CI para convertir el pipeline en un activo mantenible."
    ],
    results: [
      "Pipeline reproducible que hace visibles filas rechazadas, duplicados, nulos y frescura sin usar datos confidenciales.",
      "Contrato de datos y arquitectura cloud-ready que conecta la experiencia existente en PySpark, Big Data y GCP/AWS con prácticas modernas de plataforma.",
      "Demostración de cómo convertir una carga operativa en un producto de datos confiable para analítica, riesgo y ML."
    ],
    stack: [
      "Python",
      "pandas",
      "Parquet",
      "Streamlit",
      "pytest",
      "Docker",
      "GitHub Actions",
      "Terraform",
      "Airflow (DAG)",
      "dbt",
      "Kafka Contract",
      "Kubernetes",
      "Data Quality",
      "Observability"
    ]
  },
  {
    slug: "financial-mlops-credit-risk",
    title: "Financial MLOps Credit Risk Platform",
    summary:
      "Ciclo de vida gobernado para un modelo de riesgo crediticio sintético: entrenamiento reproducible, serving, monitoring, drift y retraining.",
    context:
      "Un modelo financiero no termina al obtener un AUC. Debe existir una ruta reproducible desde los datos y features hasta una API observable, un modelo card, umbrales explicables, revisión humana y rollback.",
    actions: [
      "Construcción de dataset sintético con variables financieras plausibles y split reproducible.",
      "Entrenamiento calibrado, métricas de ROC AUC y average precision, artefacto versionado y model card.",
      "API FastAPI con contrato de health, prediction y monitoring, además de validación de entradas.",
      "Cálculo de PSI y estados stable/warning/critical para orientar alertas y retraining.",
      "Documentación de MLflow/Vertex AI, registro de modelos, retraining, Kubernetes, fairness, adverse-action controls y rollback."
    ],
    results: [
      "Servicio reproducible que separa entrenamiento, serving y monitoring y deja trazabilidad de versión y threshold.",
      "Evidencia de MLOps aplicable a credit risk, fraud y portfolio monitoring sin revelar información bancaria.",
      "Base técnica para entrevistas de model serving, experiment tracking, drift, governance y diseño de ML systems."
    ],
    stack: [
      "Python",
      "scikit-learn",
      "FastAPI",
      "joblib",
      "pytest",
      "Docker",
      "MLflow-style Registry",
      "Retraining",
      "Kubernetes",
      "Terraform",
      "CI/CD",
      "MLOps",
      "Credit Risk",
      "Model Monitoring",
      "PSI"
    ]
  },
  {
    slug: "secure-enterprise-rag",
    title: "Secure Enterprise RAG",
    summary:
      "Sistema RAG empresarial con citas, evaluación de retrieval, redacción de PII, controles contra prompt injection y telemetría de auditoría.",
    context:
      "La brecha entre conocer LLMs y operar AI en una empresa está en la confianza: una respuesta debe estar respaldada, medirse, respetar controles de acceso y fallar de forma segura cuando no existe evidencia.",
    actions: [
      "Indexación reproducible de documentos sintéticos con IDs, títulos y metadatos de fuente.",
      "Evaluación offline con golden set, Recall@3 y MRR para detectar regresiones de retrieval.",
      "Respuesta grounded con citas, fallback de evidencia insuficiente y versionado de prompt.",
      "Bloqueo de patrones de prompt injection, redacción de PII y campos de latencia/costo/auditoría.",
      "Threat model, reranking, groundedness/citation coverage y arquitectura de evolución hacia vector search administrado, Kubernetes y model gateway."
    ],
    results: [
      "Demostración auditable de RAG que hace visible qué documento respaldó una respuesta.",
      "Controles concretos de Responsible AI y seguridad que complementan la experiencia en datos, riesgo y ciberseguridad.",
      "Evidencia de AI Engineering lista para discutir embeddings, vector stores, evaluation, guardrails, PII y cost control."
    ],
    stack: [
      "Python",
      "scikit-learn",
      "FastAPI",
      "TF-IDF Retriever",
      "pytest",
      "Docker",
      "Reranking",
      "Groundedness",
      "Citation Coverage",
      "RAG Evaluation",
      "Kubernetes",
      "Prompt Security",
      "Responsible AI",
      "Observability"
    ]
  }
];
