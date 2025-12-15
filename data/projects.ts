/*
 * Este módulo define la estructura de cada caso de estudio que se mostrará en
 * páginas dinámicas. Cada proyecto incluye un slug para la ruta, un título
 * corto, un resumen para tarjetas y secciones de contexto, acciones
 * realizadas, resultados y la pila tecnológica utilizada. Puedes ampliar
 * la información o añadir métricas adicionales según sea necesario.
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
  }
];