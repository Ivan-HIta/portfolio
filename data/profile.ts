export const profile = {
  /**
   * Información general del perfil. Estos datos se utilizan en el hero,
   * footer y metadata. Ajusta el texto para reflejar tu marca personal.
   */
  name: "Iván Moisés Hita Cahuantzi",
  // Professional headline oriented to an international audience.  It should
  // communicate that you design and build production‑grade AI/ML systems,
  // rather than just performing analytics.  Use English here to appeal
  // to global recruiters.
  headline:
    "Applied AI & Machine Learning Engineer | Building production‑grade ML systems in finance & risk",
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
      title: "AI & ML Engineering",
      desc:
        "Designing, training and deploying predictive models (Logistic, XGBoost, Deep Learning) with scalable feature stores and serving infrastructure."
    },
    {
      title: "Data & Cloud Pipelines",
      desc:
        "Building robust data pipelines on Spark, PySpark and Ab Initio; orchestrating workflows on GCP/AWS for analytics and real‑time decisioning."
    },
    {
      title: "NLP & Generative Models",
      desc:
        "Applying transformer‑based models and hybrid architectures (LLM + MLP) for text analytics, sentiment analysis and fraud detection."
    }
  ],

  /**
   * Acerca de ti. Incluye un párrafo principal y puntos destacados que
   * resuman tus fortalezas. Estos textos se pueden ampliar o ajustar.
   */
  about: {
    // Lead paragraph updated to emphasise end‑to‑end system design, MLOps
    // and the ability to translate business problems into engineered AI/ML
    // solutions.  Written in English to appeal to international recruiters.
    lead:
      "AI/ML engineer and applied researcher with a proven track record leading multidisciplinary teams and designing production‑grade models for risk, fraud and customer segmentation.  I specialise in building end‑to‑end data pipelines and translating complex business problems into scalable AI solutions.",
    bullets: [
      // Highlights emphasise system design, cloud and MLOps skills
      "Lead design and deployment of risk models using logistic regression, XGBoost and neural networks with advanced feature engineering",
      "Built and operated large‑scale data pipelines using Spark, PySpark, Ab Initio, GCP and AWS",
      "Integrated LLMs and NLP techniques into fraud detection and sentiment analysis systems in production"
    ]
  },

  /**
   * My approach to building machine learning systems.  These bullets
   * communicate engineering maturity and philosophy, showing recruiters
   * that you treat models as software and optimise for scalability,
   * maintainability and compliance.  The `approach` property is used
   * in the Approach section of the homepage.
   */
  approach: [
    "Design ML systems end‑to‑end: data ingestion, feature engineering, modelling, serving and monitoring",
    "Optimise for latency, scalability and maintainability – not just AUC or KS",
    "Treat models as software artefacts: versioned, tested and observable",
    "Balance performance with explainability, regulatory constraints and customer impact"
  ],

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