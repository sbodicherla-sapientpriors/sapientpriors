import { Card } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Info } from "lucide-react";

const tooltips: Record<string, string> = {
  locomo: "Industry benchmark for long-context conversational memory. Our system reports 91.6 overall on LoCoMo using LLM-as-judge evaluation.",
  overall: "Overall LoCoMo score across conversational memory tasks, evaluated with an LLM-as-judge rubric.",
  singleHop: "Answer a question using one remembered fact from an earlier interaction. E.g., 'I work at Stripe.' → 'Where do I work?'",
  multiHop: "Combine multiple remembered facts across conversations to answer. E.g., 'I work at Stripe.' + 'My office is in Chicago.' → 'Which city do I work in?'",
  temporal: "Reason about when events happened or which fact is most recent. E.g., 'I lived in New York.' + 'Last year, I moved to Chicago.' → 'Where did I live before Chicago?'",
  llmJudge: "LLM-as-judge evaluation uses a language model rubric to score whether answers satisfy the benchmark questions.",
  openDomain: "The model must identify which memories are relevant without topic restriction. E.g., 'I'm vegetarian.' + 'I work at Stripe.' → 'Where would be a good place for me to have lunch near work?'",
};

function InfoTooltip({ tooltipKey }: { tooltipKey: keyof typeof tooltips }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Info className="inline-block w-4 h-4 ml-1 text-muted-foreground cursor-help" />
      </TooltipTrigger>
      <TooltipContent>
        <p className="max-w-xs">{tooltips[tooltipKey]}</p>
      </TooltipContent>
    </Tooltip>
  );
}

const locomoData = [
  { metric: "Overall", tooltipKey: "overall" as const, score: 91.6 },
  { metric: "Single Hop", tooltipKey: "singleHop" as const, score: 92.3 },
  { metric: "Multi Hop", tooltipKey: "multiHop" as const, score: 93.3 },
  { metric: "Temporal", tooltipKey: "temporal" as const, score: 92.8 },
  { metric: "Open Domain", tooltipKey: "openDomain" as const, score: 76.0 },
];

const headlineCards = [
  {
    improvement: "91.6",
    metric: "LoCoMo Overall",
    subMetric: "Ours",
    tooltipKey: "locomo" as const,
    description: "LLM-as-judge evaluation",
  },
  {
    improvement: "92.8",
    metric: "Temporal Reasoning",
    tooltipKey: "temporal" as const,
    description: "Ours on LoCoMo",
  },
  {
    improvement: "93.3",
    metric: "Multi-Hop Recall",
    tooltipKey: "multiHop" as const,
    description: "Ours on LoCoMo",
  },
];

export default function BenchmarksSection() {
  return (
    <TooltipProvider>
      <section id="benchmarks" className="py-20 lg:py-32 bg-muted/50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          {/* Header */}
          <div className="text-center max-w-4xl mx-auto mb-16">
            <h2 className="text-3xl lg:text-4xl font-bold tracking-tight mb-6">
              Proven Performance
            </h2>
            <p className="text-base lg:text-lg text-muted-foreground leading-relaxed">
              Real benchmarks on industry-standard datasets, including our LoCoMo results
            </p>
          </div>

          {/* Headline Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 lg:gap-6 mb-16">
            {headlineCards.map((card, index) => (
              <Card key={index} className="p-6 text-center">
                <div className="text-3xl lg:text-4xl font-bold text-green-600 mb-2">
                  {card.improvement}
                </div>
                <div className="text-sm lg:text-base font-medium flex items-center justify-center">
                  {card.metric}
                  <InfoTooltip tooltipKey={card.tooltipKey} />
                </div>
                {"subMetric" in card && card.subMetric && (
                  <div className="text-xs text-muted-foreground mt-1">
                    {card.subMetric}
                  </div>
                )}
                {card.description && (
                  <div className="text-xs lg:text-sm text-muted-foreground mt-1">
                    {card.description}
                  </div>
                )}
              </Card>
            ))}
          </div>

          {/* Detailed Tables */}
          <div className="max-w-3xl mx-auto">
            {/* LoCoMo Table */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                LoCoMo Benchmark
                <InfoTooltip tooltipKey="locomo" />
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  (Score
                  <InfoTooltip tooltipKey="llmJudge" />)
                </span>
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2 text-sm font-medium text-muted-foreground">
                        Tasks
                      </th>
                      <th className="text-right py-3 px-2 text-sm font-medium text-green-600">
                        <div>Ours</div>
                        <div className="text-[11px] font-normal text-muted-foreground">
                          LLM-as-judge eval
                        </div>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {locomoData.map((row, index) => (
                      <tr key={index} className="border-b last:border-b-0">
                        <td className="py-3 px-2 text-sm flex items-center">
                          {row.metric}
                          <InfoTooltip tooltipKey={row.tooltipKey} />
                        </td>
                        <td className="py-3 px-2 text-sm text-right font-semibold text-green-600">
                          {row.score.toFixed(1)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>
      </section>
    </TooltipProvider>
  );
}
