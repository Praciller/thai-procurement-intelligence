import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const outputPath = resolve("data/sample/procurement_sample.csv");
mkdirSync(dirname(outputPath), { recursive: true });

const provinces = ["Bangkok", "Chiang Mai", "Phuket", "Khon Kaen", "Chonburi", "Songkhla", "Nakhon Ratchasima", "Udon Thani"];
const agencies = [
  "Sample Provincial Office A",
  "Sample Municipality B",
  "Sample Hospital C",
  "Sample Education Service Area D",
  "Sample Highway District E",
  "Sample Digital Service Center F",
  "Sample Waterworks Authority G",
  "Sample Public Health Office H",
];
const categories = ["IT", "Construction", "Medical Supplies", "Education", "Utilities", "Transport", "Office Equipment", "Public Health"];
const methods = ["e-bidding", "specific selection", "market inquiry", "e-market"];
const projectTemplates = [
  "IT network upgrade for public service office",
  "Construction of community service building",
  "Medical equipment procurement for outpatient unit",
  "School internet and classroom device upgrade",
  "Water pump maintenance and replacement",
  "Road surface improvement and traffic safety work",
  "Office computer and printer replacement",
  "ก่อสร้างระบบระบายน้ำชุมชนตัวอย่าง",
  "IT cybersecurity monitoring subscription",
  "Solar lighting installation for public area",
];

const header = [
  "source_record_id",
  "project_name",
  "agency_name",
  "province",
  "procurement_method",
  "procurement_category",
  "budget_amount",
  "winning_amount",
  "winner_name",
  "announcement_date",
  "contract_date",
  "source_url",
  "raw_text",
];

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const rows = [header.join(",")];
for (let index = 1; index <= 120; index += 1) {
  const province = provinces[index % provinces.length];
  const agency = agencies[index % agencies.length];
  const category = categories[index % categories.length];
  const method = methods[index % methods.length];
  const projectName = `${projectTemplates[index % projectTemplates.length]} ${String(index).padStart(3, "0")}`;
  const budget = 250000 + index * 73500 + (index % 9) * 18000;
  const winning = Math.round(budget * (0.86 + (index % 7) * 0.015));
  const month = String((index % 12) + 1).padStart(2, "0");
  const day = String((index % 27) + 1).padStart(2, "0");
  const contractDay = String(((index + 12) % 27) + 1).padStart(2, "0");
  const rawText = [
    "Sample/demo procurement record only.",
    `Agency ${agency} plans ${projectName}.`,
    `Category ${category}; method ${method}; province ${province}.`,
    "No real agency claim is made.",
  ].join(" ");
  rows.push(
    [
      `SAMPLE-${String(index).padStart(4, "0")}`,
      projectName,
      agency,
      province,
      method,
      category,
      budget,
      winning,
      `Sample Vendor ${String.fromCharCode(65 + (index % 12))}`,
      `2025-${month}-${day}`,
      `2025-${month}-${contractDay}`,
      `https://example.org/sample-procurement/${index}`,
      rawText,
    ]
      .map(csvEscape)
      .join(","),
  );
}

writeFileSync(outputPath, `${rows.join("\n")}\n`, "utf8");
console.log(`Wrote ${rows.length - 1} sample records to ${outputPath}`);

