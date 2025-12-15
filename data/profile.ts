export const profile = {
  /**
   * Información general del perfil. Estos datos se utilizan en el hero,
   * footer y metadata. Ajusta el texto para reflejar tu marca personal.
   */
  name: "Iván Moisés Hita Cahuantzi",
  headline:
    "Líder en Ciencia de Datos y Riesgo Crediticio | ML Avanzado & Ingeniería de Datos | Banca y Retail",
  roles: [
    "Data Science Coordinator (El Puerto de Liverpool)",
    "Senior Data Scientist (Citibanamex)",
    "Risk Intelligence Analyst"
  ],
  location: "Ciudad de México, México",
  email: "ivan_hita@outlook.com",
  links: {
    linkedin:
      "https://www.linkedin.com/in/iv%C3%A1n-mois%C3%A9s-hita-1b9666175/",
    github: "https://github.com/Ivan-HIta"
  },

  /**
   * Servicios o líneas de experiencia que ofreces. Se muestran como
   * tarjetas en la sección de experiencia.
   */
  services: [
    {
      title: "Modelado de Riesgo Crediticio",
      desc:
        "Diseño y despliegue de modelos predictivos (Logistic, XGBoost, MLP) que incrementan aprobaciones y reducen morosidad."
    },
    {
      title: "Ingeniería de Datos & Nube",
      desc:
        "Construcción de pipelines de datos en Spark, PySpark, Ab Initio y orquestación en GCP/AWS para procesos de riesgo y analítica."
    },
    {
      title: "NLP & Modelos Generativos",
      desc:
        "Aplicación de Transformers y modelos híbridos (LLM+MLP) para analítica de texto, sentiment analysis y detección de fraude."
    }
  ],

  /**
   * Acerca de ti. Incluye un párrafo principal y puntos destacados que
   * resuman tus fortalezas. Estos textos se pueden ampliar o ajustar.
   */
  about: {
    lead:
      "Científico de datos con experiencia liderando equipos multidisciplinarios y desarrollando modelos de riesgo, fraude y segmentación en banca y retail. Especialista en pipelines de Big Data y en traducir las necesidades del negocio en soluciones de IA de alto impacto.",
    bullets: [
      "Conducción de proyectos de modelado de riesgo: logistic regression con Elastic Net, XGBoost, MLP y GA",
      "Implementación de pipelines en Big Data: Spark, PySpark, Ab Initio, GCP y AWS",
      "Integración de modelos generativos y NLP para detección de fraude y análisis de sentimientos"
    ]
  },

  /**
   * Skills listados como chips. Agrega o elimina según tus competencias. Se
   * recomienda enfocarse en las habilidades más relevantes para tu rol."
   */
  skills: [
    "Python",
    "SAS",
    "SQL",
    "Spark / PySpark",
    "Ab Initio",
    "GCP",
    "AWS",
    "Snowflake",
    "Scala",
    "R",
    "Go",
    "Julia",
    "Tableau / Power BI",
    "Prompt Engineering",
    "ML Ops",
    "Feature Engineering",
    "XGBoost",
    "Elastic Net",
    "Genetic Algorithms",
    "Transformers"
  ],

  /**
   * Proyectos destacados. Estos aparecerán como tarjetas en la sección de
   * trabajo y enlazarán a páginas con más detalle. El slug debe coincidir
   * con la ruta generada en data/projects.ts.
   */
  work: [
    {
      slug: "modelo-riesgo-nomina",
      title: "Modelo de Riesgo de Préstamos de Nómina",
      subtitle:
        "Mejora del scorecard tradicional usando Logistic Regression + Elastic Net + GA",
      tags: ["#LogisticRegression", "#ElasticNet", "#GeneticAlgorithms", "#PySpark"],
      links: { code: "", demo: "" }
    },
    {
      slug: "modelo-prestamo-personal-xgboost",
      title: "Modelo de Riesgo de Préstamos Personales",
      subtitle:
        "XGBoost y optimización bayesiana para discriminar solicitantes y aumentar aprobaciones",
      tags: ["#XGBoost", "#BayesianOptimization", "#AWS", "#SHAP"],
      links: { code: "", demo: "" }
    },
    {
      slug: "modelo-nomina-no-hit-mlp",
      title: "Modelo Nómina para No‑Hit",
      subtitle:
        "MLP + Propensity Score Matching + GA para clientes sin historial crediticio",
      tags: ["#MLP", "#PSM", "#GA", "#PyTorch", "#PySpark"],
      links: { code: "", demo: "" }
    },
    {
      slug: "segmentacion-primacia",
      title: "Segmentación de Clientes por Primacía",
      subtitle:
        "Clustering de comportamiento para identificar lealtad y orientar marketing",
      tags: ["#Clustering", "#KMeans", "#Primacy", "#BehaviouralAnalytics"],
      links: { code: "", demo: "" }
    },
    {
      slug: "analisis-sentimientos-cobranza",
      title: "Análisis de Sentimientos para Cobranza",
      subtitle:
        "Modelo BETO para priorizar recuperaciones y mejorar experiencia de clientes",
      tags: ["#BETO", "#NLP", "#SentimentAnalysis", "#Collections"],
      links: { code: "", demo: "" }
    },
    {
      slug: "deteccion-fraude-llm-mlp",
      title: "Detección de Fraude en Transferencias",
      subtitle:
        "Modelo híbrido LLM + MLP para prevenir fraude sin afectar a clientes legítimos",
      tags: ["#LLM", "#MLP", "#FraudDetection", "#MLOps"],
      links: { code: "", demo: "" }
    }
  ],

  /**
   * Lista de certificaciones y cursos relevantes. Muestra el título y el
   * emisor. Puedes ampliar o reducir según tu gusto.
   */
  certifications: [
    {
      title: "SAS Statistical Business Analyst",
      issuer: "SAS Institute (Coursera), 2021"
    },
    {
      title: "Snowflake Data Engineering Professional Certificate",
      issuer: "Snowflake Northstar (Coursera), 2025"
    },
    {
      title: "IBM Data Engineering Professional Certificate",
      issuer: "IBM (Coursera), 2025"
    },
    { title: "LLMOps Specialization", issuer: "Duke University (Coursera), 2025" },
    {
      title: "TensorFlow Developer Professional Certificate",
      issuer: "DeepLearning.AI (Coursera), 2022"
    },
    {
      title: "AWS Cloud Solutions Architect",
      issuer: "Amazon (Coursera), 2024"
    },
    {
      title: "Functional Programming in Scala",
      issuer: "École Polytechnique Fédérale de Lausanne (Coursera), 2024"
    }
  ]
};