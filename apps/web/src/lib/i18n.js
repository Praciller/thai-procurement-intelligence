export const defaultLocale = "en";

export const languages = [
  { id: "en", shortLabel: "EN", label: "English" },
  { id: "th", shortLabel: "TH", label: "ไทย" },
];

const dictionaries = {
  en: {
    shell: {
      product: "Thai Procurement Intelligence",
      subtitle: "Sample public-data AI platform",
      languageLabel: "Language",
      nav: {
        home: "Home",
        search: "Search",
        dashboard: "Dashboard",
        assistant: "Assistant",
        dataStatus: "Data Status",
        about: "About",
      },
    },
    common: {
      demoNotice:
        "This demo uses synthetic sample records with obvious sample agency and vendor names. It does not claim facts about real agencies.",
      notAvailable: "Not available",
      uncategorized: "Uncategorized",
      unknownAgency: "Unknown agency",
      unknownProvince: "Unknown province",
      source: "Source",
    },
    table: {
      project: "Project",
      agency: "Agency",
      province: "Province",
      budget: "Budget",
      date: "Date",
      noRecordsTitle: "No records found",
      noRecordsBody: "Run sample ingestion or adjust the search filters.",
    },
    home: {
      title: "AI-powered search for Thai public procurement data",
      description:
        "A portfolio-grade data product that ingests public or sample procurement records, normalizes them, supports search and analytics, and answers questions with cited evidence.",
      searchRecords: "Search records",
      askAssistant: "Ask assistant",
      stats: {
        records: "Records",
        afterIngestion: "After ingestion",
        totalBudget: "Total budget",
        sampleDataOnly: "Sample data only",
        averageBudget: "Average budget",
        normalizedNumericField: "Normalized numeric field",
      },
      recordsByProvince: "Records by province",
      topProjects: "Highest budget sample projects",
      noProvinceData: "Province distribution appears after records are loaded.",
    },
    recordsPage: {
      title: "Procurement Search",
      description:
        "Search sample procurement records by keyword, province, category, budget order, and search mode. Semantic and hybrid modes degrade to deterministic local retrieval when vector infrastructure is not configured.",
    },
    recordsClient: {
      keyword: "Keyword",
      keywordPlaceholder: "IT, construction, hospital",
      province: "Province",
      allProvinces: "All provinces",
      category: "Category",
      allCategories: "All categories",
      searchMode: "Search mode",
      sort: "Sort",
      exportCsv: "Export CSV",
      updatingResults: "Updating results...",
      records: "records",
      noApiTitle: "No API data yet",
      noApiBody: "API returned no records. Run sample ingestion from the README command.",
      modeLabels: {
        keyword: "keyword",
        semantic: "semantic",
        hybrid: "hybrid",
      },
      sortOptions: {
        date_desc: "Newest first",
        date_asc: "Oldest first",
        budget_desc: "Budget high to low",
        budget_asc: "Budget low to high",
      },
    },
    dashboard: {
      title: "Analytics Dashboard",
      description:
        "Overview metrics from normalized procurement records: budget totals, province distribution, categories, agencies, monthly volume, and high-budget projects.",
      totalRecords: "Total records",
      totalBudget: "Total budget",
      averageBudget: "Average budget",
      provinceDistribution: "Province distribution",
      categoryDistribution: "Category distribution",
      monthlyVolume: "Monthly volume",
      topAgencies: "Top agencies",
      topBudgetProjects: "Top budget projects",
    },
    assistantPage: {
      title: "AI Assistant",
      description:
        "Ask natural-language questions. The backend retrieves procurement records first, then uses the configured LLM provider only when enabled.",
    },
    assistantClient: {
      question: "Question",
      guardrail: "Answers are constrained to retrieved procurement records and citations.",
      ask: "Ask",
      asking: "Asking...",
      unavailableTitle: "Assistant unavailable",
      unavailableBody: "Assistant request failed. Confirm API is running and sample data has been ingested.",
      answer: "Answer",
      disabled: "LLM generation is disabled; retrieved evidence is still shown.",
      retrievedEvidence: "Retrieved evidence",
      exampleQuestions: "Example questions",
      examples: [
        "What are the highest-budget IT procurement projects?",
        "Which agencies have many construction projects?",
        "Summarize procurement records in Bangkok.",
      ],
    },
    dataStatus: {
      title: "Data Status",
      description: "Read-only operational view for ingestion runs, record counts, sample source status, and demo readiness.",
      records: "Records",
      ingestionRuns: "Ingestion runs",
      latestStatus: "Latest status",
      noRun: "No run",
      recentRuns: "Recent ingestion runs",
      source: "Source",
      status: "Status",
      rows: "Rows",
      inserted: "Inserted",
      updated: "Updated",
      failed: "Failed",
      finished: "Finished",
      emptyTitle: "No ingestion runs yet",
      emptyBody: "Run the sample import command to populate the database and display import counters.",
    },
    about: {
      title: "Methodology",
      description: "Architecture and operating constraints for a personal portfolio project focused on AI engineering and data engineering.",
      items: [
        {
          title: "Data source strategy",
          body:
            "The MVP ships with synthetic but realistic sample procurement records and a CSV ingestion interface. Public CSV, Excel, and API adapters are isolated behind data-source interfaces so real open data can replace the sample source.",
        },
        {
          title: "AI design",
          body:
            "LLM calls are optional, provider-based, and evidence limited. Gemini and OpenRouter providers sit behind the same interface as the deterministic mock provider, and summaries are cached in the database.",
        },
        {
          title: "Cost control",
          body:
            "The demo works without private API keys. Embeddings use a local deterministic fallback, summary generation is cached, and deployment targets free-tier Vercel, hosted FastAPI, and Supabase PostgreSQL.",
        },
        {
          title: "Privacy boundary",
          body:
            "Only public or sample procurement records are designed to be sent to AI providers. No employer, company, or confidential data is required or included.",
        },
      ],
    },
    detail: {
      budget: "Budget",
      winningAmount: "Winning amount",
      announcement: "Announcement",
      method: "Method",
      rawSourceText: "Raw source text",
      noRawSourceText: "No raw source text available.",
      similarRecords: "Similar records",
      normalizedFields: "Normalized fields",
      recordId: "Record ID",
      agency: "Agency",
      province: "Province",
      category: "Category",
      winner: "Winner",
      contractDate: "Contract date",
      imported: "Imported",
      updated: "Updated",
      notFoundTitle: "Record not found",
      notFoundBody: "The API did not return this procurement record. It may not be ingested yet.",
    },
    summary: {
      title: "AI Summary",
      cachedSummary: "Cached summary",
      noSummary: "No summary generated",
      generating: "Generating summary...",
      returnedCached: "Returned cached summary",
      generatedWith: "Generated with",
      unavailable: "AI summary unavailable. Check ENABLE_LLM or use mock provider for local demo.",
      refresh: "Refresh",
      generate: "Generate",
      placeholder:
        "Generate a concise evidence-limited summary. If no LLM key is configured, the backend can use the deterministic mock provider for local testing.",
    },
  },
  th: {
    shell: {
      product: "Thai Procurement Intelligence",
      subtitle: "แพลตฟอร์ม AI จากข้อมูลสาธารณะตัวอย่าง",
      languageLabel: "ภาษา",
      nav: {
        home: "หน้าแรก",
        search: "ค้นหา",
        dashboard: "แดชบอร์ด",
        assistant: "ผู้ช่วย",
        dataStatus: "สถานะข้อมูล",
        about: "เกี่ยวกับ",
      },
    },
    common: {
      demoNotice:
        "เดโมนี้ใช้ระเบียนจัดซื้อจัดจ้างตัวอย่างที่สร้างขึ้นพร้อมชื่อหน่วยงานและผู้ขายแบบตัวอย่างเท่านั้น ไม่ได้อ้างข้อเท็จจริงเกี่ยวกับหน่วยงานจริง",
      notAvailable: "ไม่มีข้อมูล",
      uncategorized: "ไม่ระบุหมวดหมู่",
      unknownAgency: "ไม่ทราบหน่วยงาน",
      unknownProvince: "ไม่ทราบจังหวัด",
      source: "แหล่งข้อมูล",
    },
    table: {
      project: "โครงการ",
      agency: "หน่วยงาน",
      province: "จังหวัด",
      budget: "งบประมาณ",
      date: "วันที่",
      noRecordsTitle: "ไม่พบระเบียน",
      noRecordsBody: "นำเข้าข้อมูลตัวอย่างหรือปรับตัวกรองการค้นหา",
    },
    home: {
      title: "ค้นหาและวิเคราะห์ข้อมูลจัดซื้อจัดจ้างภาครัฐไทยด้วย AI",
      description:
        "ผลิตภัณฑ์ข้อมูลสำหรับพอร์ตโฟลิโอที่นำเข้าระเบียนจัดซื้อจัดจ้างสาธารณะหรือตัวอย่าง ทำข้อมูลให้เป็นมาตรฐาน รองรับการค้นหา วิเคราะห์ และตอบคำถามพร้อมหลักฐานอ้างอิง",
      searchRecords: "ค้นหาระเบียน",
      askAssistant: "ถามผู้ช่วย",
      stats: {
        records: "ระเบียน",
        afterIngestion: "หลังนำเข้าข้อมูล",
        totalBudget: "งบประมาณรวม",
        sampleDataOnly: "ข้อมูลตัวอย่างเท่านั้น",
        averageBudget: "งบประมาณเฉลี่ย",
        normalizedNumericField: "ฟิลด์ตัวเลขที่ทำมาตรฐานแล้ว",
      },
      recordsByProvince: "ระเบียนตามจังหวัด",
      topProjects: "โครงการตัวอย่างงบประมาณสูงสุด",
      noProvinceData: "การกระจายตามจังหวัดจะแสดงหลังโหลดระเบียน",
    },
    recordsPage: {
      title: "ค้นหาระเบียนจัดซื้อจัดจ้าง",
      description:
        "ค้นหาระเบียนตัวอย่างด้วยคำค้น จังหวัด หมวดหมู่ ลำดับงบประมาณ และโหมดค้นหา โหมด semantic และ hybrid จะถอยกลับเป็นการค้นหาแบบกำหนดได้เมื่อยังไม่ได้ตั้งค่าเวกเตอร์",
    },
    recordsClient: {
      keyword: "คำค้น",
      keywordPlaceholder: "IT, ก่อสร้าง, โรงพยาบาล",
      province: "จังหวัด",
      allProvinces: "ทุกจังหวัด",
      category: "หมวดหมู่",
      allCategories: "ทุกหมวดหมู่",
      searchMode: "โหมดค้นหา",
      sort: "จัดเรียง",
      exportCsv: "ส่งออก CSV",
      updatingResults: "กำลังอัปเดตผลลัพธ์...",
      records: "ระเบียน",
      noApiTitle: "ยังไม่มีข้อมูลจาก API",
      noApiBody: "API ไม่ส่งคืนระเบียน โปรดรันคำสั่งนำเข้าข้อมูลตัวอย่างจาก README",
      modeLabels: {
        keyword: "คำค้น",
        semantic: "ความหมาย",
        hybrid: "ผสม",
      },
      sortOptions: {
        date_desc: "ใหม่สุดก่อน",
        date_asc: "เก่าสุดก่อน",
        budget_desc: "งบมากไปน้อย",
        budget_asc: "งบน้อยไปมาก",
      },
    },
    dashboard: {
      title: "แดชบอร์ดวิเคราะห์",
      description:
        "ตัวชี้วัดภาพรวมจากระเบียนจัดซื้อจัดจ้างที่ทำมาตรฐานแล้ว: งบประมาณรวม การกระจายตามจังหวัด หมวดหมู่ หน่วยงาน ปริมาณรายเดือน และโครงการงบสูง",
      totalRecords: "ระเบียนทั้งหมด",
      totalBudget: "งบประมาณรวม",
      averageBudget: "งบประมาณเฉลี่ย",
      provinceDistribution: "การกระจายตามจังหวัด",
      categoryDistribution: "การกระจายตามหมวดหมู่",
      monthlyVolume: "ปริมาณรายเดือน",
      topAgencies: "หน่วยงานอันดับต้น",
      topBudgetProjects: "โครงการงบประมาณสูงสุด",
    },
    assistantPage: {
      title: "ผู้ช่วย AI",
      description:
        "ถามคำถามภาษาธรรมชาติ ระบบหลังบ้านจะค้นระเบียนจัดซื้อจัดจ้างก่อน แล้วจึงใช้ผู้ให้บริการ LLM ที่ตั้งค่าไว้เมื่อเปิดใช้งาน",
    },
    assistantClient: {
      question: "คำถาม",
      guardrail: "คำตอบจำกัดอยู่กับระเบียนที่ค้นคืนได้และมีการอ้างอิง",
      ask: "ถาม",
      asking: "กำลังถาม...",
      unavailableTitle: "ผู้ช่วยไม่พร้อมใช้งาน",
      unavailableBody: "คำขอผู้ช่วยล้มเหลว โปรดยืนยันว่า API ทำงานและนำเข้าข้อมูลตัวอย่างแล้ว",
      answer: "คำตอบ",
      disabled: "ปิดการสร้างคำตอบด้วย LLM อยู่ แต่ยังแสดงหลักฐานที่ค้นคืนได้",
      retrievedEvidence: "หลักฐานที่ค้นคืนได้",
      exampleQuestions: "ตัวอย่างคำถาม",
      examples: [
        "โครงการจัดซื้อ IT ที่มีงบประมาณสูงสุดคืออะไร?",
        "หน่วยงานใดมีโครงการก่อสร้างจำนวนมาก?",
        "สรุประเบียนจัดซื้อจัดจ้างในกรุงเทพฯ",
      ],
    },
    dataStatus: {
      title: "สถานะข้อมูล",
      description: "มุมมองปฏิบัติการแบบอ่านอย่างเดียวสำหรับรอบนำเข้า จำนวนระเบียน สถานะแหล่งข้อมูลตัวอย่าง และความพร้อมของเดโม",
      records: "ระเบียน",
      ingestionRuns: "รอบนำเข้า",
      latestStatus: "สถานะล่าสุด",
      noRun: "ยังไม่มีรอบ",
      recentRuns: "รอบนำเข้าล่าสุด",
      source: "แหล่งข้อมูล",
      status: "สถานะ",
      rows: "แถว",
      inserted: "เพิ่ม",
      updated: "อัปเดต",
      failed: "ล้มเหลว",
      finished: "เสร็จสิ้น",
      emptyTitle: "ยังไม่มีรอบนำเข้า",
      emptyBody: "รันคำสั่งนำเข้าตัวอย่างเพื่อเติมฐานข้อมูลและแสดงตัวนับการนำเข้า",
    },
    about: {
      title: "วิธีการทำงาน",
      description: "สถาปัตยกรรมและข้อจำกัดการปฏิบัติงานสำหรับโปรเจกต์พอร์ตโฟลิโอส่วนตัวด้าน AI engineering และ data engineering",
      items: [
        {
          title: "กลยุทธ์แหล่งข้อมูล",
          body:
            "MVP มาพร้อมระเบียนจัดซื้อจัดจ้างตัวอย่างที่สมจริงและอินเทอร์เฟซนำเข้า CSV อะแดปเตอร์สำหรับ CSV, Excel และ API สาธารณะถูกแยกไว้หลังอินเทอร์เฟซแหล่งข้อมูลเพื่อให้แทนที่ด้วยข้อมูลเปิดจริงได้",
        },
        {
          title: "การออกแบบ AI",
          body:
            "การเรียก LLM เป็นทางเลือก แยกตามผู้ให้บริการ และจำกัดตามหลักฐาน Gemini และ OpenRouter ใช้อินเทอร์เฟซเดียวกับ mock provider แบบกำหนดได้ และสรุปจะถูกแคชในฐานข้อมูล",
        },
        {
          title: "ควบคุมต้นทุน",
          body:
            "เดโมทำงานได้โดยไม่ต้องใช้คีย์ส่วนตัว Embedding มี fallback แบบกำหนดได้ในเครื่อง การสร้างสรุปถูกแคช และเป้าหมาย deploy ใช้ free tier ของ Vercel, FastAPI และ Supabase PostgreSQL",
        },
        {
          title: "ขอบเขตความเป็นส่วนตัว",
          body:
            "ออกแบบให้ส่งเฉพาะข้อมูลจัดซื้อจัดจ้างสาธารณะหรือตัวอย่างไปยังผู้ให้บริการ AI ไม่ต้องใช้หรือรวมข้อมูลนายจ้าง บริษัท หรือข้อมูลลับ",
        },
      ],
    },
    detail: {
      budget: "งบประมาณ",
      winningAmount: "วงเงินชนะ",
      announcement: "ประกาศ",
      method: "วิธีการ",
      rawSourceText: "ข้อความต้นทางดิบ",
      noRawSourceText: "ไม่มีข้อความต้นทางดิบ",
      similarRecords: "ระเบียนที่คล้ายกัน",
      normalizedFields: "ฟิลด์ที่ทำมาตรฐาน",
      recordId: "รหัสระเบียน",
      agency: "หน่วยงาน",
      province: "จังหวัด",
      category: "หมวดหมู่",
      winner: "ผู้ชนะ",
      contractDate: "วันที่สัญญา",
      imported: "นำเข้า",
      updated: "อัปเดต",
      notFoundTitle: "ไม่พบระเบียน",
      notFoundBody: "API ไม่ส่งคืนระเบียนนี้ อาจยังไม่ถูกนำเข้า",
    },
    summary: {
      title: "สรุปด้วย AI",
      cachedSummary: "สรุปจากแคช",
      noSummary: "ยังไม่มีสรุป",
      generating: "กำลังสร้างสรุป...",
      returnedCached: "ส่งคืนสรุปจากแคช",
      generatedWith: "สร้างด้วย",
      unavailable: "สรุปด้วย AI ไม่พร้อมใช้งาน โปรดตรวจ ENABLE_LLM หรือใช้ mock provider สำหรับเดโมในเครื่อง",
      refresh: "รีเฟรช",
      generate: "สร้าง",
      placeholder:
        "สร้างสรุปสั้นแบบจำกัดตามหลักฐาน หากไม่ได้ตั้งค่า LLM key ระบบหลังบ้านสามารถใช้ mock provider แบบกำหนดได้สำหรับการทดสอบในเครื่อง",
    },
  },
};

export function normalizeLocale(locale) {
  const value = Array.isArray(locale) ? locale[0] : locale;
  return value === "th" ? "th" : defaultLocale;
}

export function getDictionary(locale) {
  return dictionaries[normalizeLocale(locale)];
}

export function withLocale(href, locale) {
  const normalizedLocale = normalizeLocale(locale);
  const [withoutHash, hash] = href.split("#");
  const [pathname, query = ""] = withoutHash.split("?");
  const params = new URLSearchParams(query);
  params.set("lang", normalizedLocale);
  const nextQuery = params.toString();
  return `${pathname}${nextQuery ? `?${nextQuery}` : ""}${hash ? `#${hash}` : ""}`;
}
