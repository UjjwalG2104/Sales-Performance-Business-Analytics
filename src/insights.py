"""
SalesIQ — Automated Business Intelligence & Actionable Insights Engine.
Synthesizes multi-dimensional data findings into a structured 4-pillar executive framework:
1. What happened?
2. What evidence supports the finding?
3. Why might it matter to the business? (labeled hypotheses)
4. What action could the business consider?
Formatted throughout with Indian Rupee (₹) standards.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from src.formatters import format_indian_number, format_inr


@dataclass
class BusinessInsight:
    category: str
    headline: str
    severity: str  # 'positive', 'warning', 'critical', 'info'
    what_happened: str
    evidence: str
    why_it_matters: str
    recommended_action: str


class InsightsGenerator:
    """
    Evaluates the active dataset and dynamically generates evidence-backed business insights.
    """

    @staticmethod
    def generate_all_insights(df: pd.DataFrame, currency_symbol: str = "₹") -> List[BusinessInsight]:
        """Runs rule-based analytical checks on the dataset and returns structured insights."""
        if df is None or df.empty or "Sales" not in df.columns:
            return []

        insights: List[BusinessInsight] = []
        has_profit = "Profit" in df.columns
        has_discount = "Discount" in df.columns
        has_dates = "Order Date" in df.columns

        # 1. Top Revenue-Generating Category
        if "Category" in df.columns:
            agg_dict = {"Sales": ("Sales", "sum")}
            if has_profit:
                agg_dict["Profit"] = ("Profit", "sum")

            cat_summary = df.groupby("Category").agg(**agg_dict).reset_index()
            total_sales = cat_summary["Sales"].sum()
            if total_sales > 0:
                top_cat = cat_summary.sort_values("Sales", ascending=False).iloc[0]
                cat_share = (top_cat["Sales"] / total_sales) * 100.0
                sales_str = format_inr(top_cat["Sales"], symbol=currency_symbol)

                if has_profit:
                    cat_margin = (top_cat["Profit"] / top_cat["Sales"]) * 100.0 if top_cat["Sales"] > 0 else 0.0
                    profit_str = format_inr(top_cat["Profit"], symbol=currency_symbol)
                    evidence_str = f"Generated {sales_str} ({cat_share:.1f}% of total portfolio revenue) with a {cat_margin:.1f}% profit margin ({profit_str} net profit)."
                    severity = "positive" if cat_margin >= 15 else "info"
                else:
                    evidence_str = f"Generated {sales_str} ({cat_share:.1f}% of total portfolio revenue)."
                    severity = "info"

                insights.append(BusinessInsight(
                    category="Product Strategy",
                    headline=f"Leading Revenue Driver: {top_cat['Category']}",
                    severity=severity,
                    what_happened=f"{top_cat['Category']} is the business's largest revenue contributor.",
                    evidence=evidence_str,
                    why_it_matters="Hypothesis: High market demand and category brand recognition make this the core cash cow. However, portfolio over-reliance leaves the business vulnerable to supply disruption or competitor price warfare.",
                    recommended_action="Protect key supplier contracts, evaluate cross-selling opportunities with high-margin accessories, and bundle slower-moving items."
                ))

        # 2. Regional Profitability Disparity & Best Region
        if "Region" in df.columns and len(df["Region"].dropna().unique()) > 1:
            reg_agg = {"Sales": ("Sales", "sum")}
            if has_profit:
                reg_agg["Profit"] = ("Profit", "sum")
            reg_summary = df.groupby("Region").agg(**reg_agg).reset_index()

            if has_profit:
                reg_summary["Margin"] = (reg_summary["Profit"] / reg_summary["Sales"].replace(0, np.nan)) * 100.0
                best_reg = reg_summary.sort_values("Profit", ascending=False).iloc[0]
                worst_reg = reg_summary.sort_values("Profit", ascending=True).iloc[0]

                best_prof_str = format_inr(best_reg["Profit"], symbol=currency_symbol)
                worst_prof_str = format_inr(worst_reg["Profit"], symbol=currency_symbol)

                insights.append(BusinessInsight(
                    category="Geographic Operations",
                    headline=f"Regional Performance Split: {best_reg['Region']} vs {worst_reg['Region']}",
                    severity="positive" if worst_reg["Profit"] >= 0 else "warning",
                    what_happened=f"{best_reg['Region']} is delivering peak operating profit, while {worst_reg['Region']} is lagging behind.",
                    evidence=f"{best_reg['Region']} generated {best_prof_str} in profit ({best_reg['Margin']:.1f}% margin) vs {worst_reg['Region']} generating {worst_prof_str} ({worst_reg['Margin']:.1f}% margin).",
                    why_it_matters="Hypothesis: Geographic variations in distribution costs, local discount aggression, or regional product mix are causing substantial margin divergence.",
                    recommended_action=f"Benchmark operational practices from {best_reg['Region']} and conduct an audit of localized pricing and fulfillment contracts in {worst_reg['Region']}."
                ))
            else:
                top_reg = reg_summary.sort_values("Sales", ascending=False).iloc[0]
                top_sales_str = format_inr(top_reg["Sales"], symbol=currency_symbol)
                insights.append(BusinessInsight(
                    category="Geographic Operations",
                    headline=f"Top Performing Territory: {top_reg['Region']}",
                    severity="info",
                    what_happened=f"{top_reg['Region']} is leading in sales volume across all recorded regions.",
                    evidence=f"Delivered {top_sales_str} in gross sales.",
                    why_it_matters="Hypothesis: Favorable demographic density or mature local distribution channels drive higher territory conversion.",
                    recommended_action="Scale marketing investments in top-performing regions while investigating distribution bottlenecks in smaller markets."
                ))

        # 3. Toxic Discounting & Negative Margin Outliers (Requires Profit & Discount)
        if has_discount and has_profit:
            negative_profit_df = df[df["Profit"] < 0]
            if not negative_profit_df.empty:
                loss_total = abs(negative_profit_df["Profit"].sum())
                loss_sales = negative_profit_df["Sales"].sum()
                avg_loss_discount = negative_profit_df["Discount"].mean() * 100.0
                profitable_discount = df[df["Profit"] >= 0]["Discount"].mean() * 100.0 if (df["Profit"] >= 0).any() else 0.0

                loss_sales_str = format_inr(loss_sales, symbol=currency_symbol)
                loss_total_str = format_inr(-loss_total, symbol=currency_symbol)

                insights.append(BusinessInsight(
                    category="Pricing & Margins",
                    headline="Unprofitable Transactions Due to Deep Discounting",
                    severity="critical",
                    what_happened="Substantial volume of transactions are realizing negative operating profit.",
                    evidence=f"{format_indian_number(len(negative_profit_df))} transactions ({loss_sales_str} sales) generated cumulative net losses of {loss_total_str}. The average discount on loss-making orders was {avg_loss_discount:.1f}% vs {profitable_discount:.1f}% on profitable sales.",
                    why_it_matters="Hypothesis: Sales reps or automatic clearance promotions are offering discounts beyond gross margin thresholds, effectively subsidizing client purchases at a company loss.",
                    recommended_action="Implement hard discount caps (e.g., maximum 20% without regional manager authorization) and automate cart-level margin warnings before checkout."
                ))

        # 4. High-Volume, Margin-Diluting Products (Requires Profit and Product column)
        prod_col = "Product Name" if "Product Name" in df.columns else ("Product ID" if "Product ID" in df.columns else None)
        if prod_col and has_profit:
            prod_summary = df.groupby(prod_col).agg(
                Sales=("Sales", "sum"),
                Profit=("Profit", "sum")
            ).reset_index()
            prod_summary["Margin"] = (prod_summary["Profit"] / prod_summary["Sales"].replace(0, np.nan)) * 100.0

            diluters = prod_summary[(prod_summary["Sales"] > prod_summary["Sales"].median()) & (prod_summary["Margin"] < 3.0)]
            if not diluters.empty:
                worst_diluter = diluters.sort_values("Sales", ascending=False).iloc[0]
                dil_sales_str = format_inr(worst_diluter["Sales"], symbol=currency_symbol)
                dil_prof_str = format_inr(worst_diluter["Profit"], symbol=currency_symbol)
                insights.append(BusinessInsight(
                    category="Merchandising & Inventory",
                    headline=f"Margin Diluter Detected: {str(worst_diluter[prod_col])[:35]}...",
                    severity="warning",
                    what_happened="A top-selling item is generating high sales volume with near-zero or negative margin.",
                    evidence=f"Product generated {dil_sales_str} in sales, but yielded only {dil_prof_str} profit ({worst_diluter['Margin']:.1f}% net margin).",
                    why_it_matters="Hypothesis: High freight overheads, competitive price-matching, or supplier cost increases have compressed unit economics on a high-velocity item.",
                    recommended_action="Renegotiate vendor wholesale pricing, recalibrate shipping surcharges, or raise price points marginally (1-3%) to test price elasticity."
                ))

        # 5. Month with Peak Seasonality
        if has_dates:
            temp = df.copy()
            temp["Order Date"] = pd.to_datetime(temp["Order Date"], errors="coerce")
            temp = temp.dropna(subset=["Order Date"])
            if not temp.empty:
                temp["YearMonth"] = temp["Order Date"].dt.strftime("%B %Y")
                monthly_sales = temp.groupby("YearMonth", sort=False)["Sales"].sum()
                if len(monthly_sales) > 1:
                    peak_month = monthly_sales.idxmax()
                    peak_value = monthly_sales.max()
                    avg_month = monthly_sales.mean()
                    spike_pct = ((peak_value - avg_month) / avg_month) * 100.0 if avg_month > 0 else 0.0

                    peak_val_str = format_inr(peak_value, symbol=currency_symbol)
                    avg_val_str = format_inr(avg_month, symbol=currency_symbol)

                    insights.append(BusinessInsight(
                        category="Demand & Seasonality",
                        headline=f"Peak Sales Month: {peak_month}",
                        severity="info",
                        what_happened=f"{peak_month} recorded the highest monthly sales revenue in the dataset.",
                        evidence=f"Revenue reached {peak_val_str}, representing a +{spike_pct:.1f}% surge over the average monthly baseline of {avg_val_str}.",
                        why_it_matters="Hypothesis: Year-end corporate budget flush, holiday retail demand, or seasonal promotions created an acute concentration of order activity.",
                        recommended_action="Prepare inventory replenishment 60 days ahead of this seasonal window and optimize carrier contracts to avoid peak-season shipping surcharges."
                    ))

        return insights
