// DATA CONFIGURATION
const EMBEDDED_DATA = null; // Will be replaced by Python script

// SVG Icons as strings
const Icons = {
  calendar:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
  star: '<svg class="icon icon-sm" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
  messageSquare:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
  clock:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  trendingUp:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
  trendingDown:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/><polyline points="17 18 23 18 23 12"/></svg>',
  checkCircle:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  xCircle:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
  edit: '<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
  tag: '<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
  thumbsUp:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>',
  thumbsDown:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>',
  refresh:
    '<svg class="icon icon-sm" viewBox="0 0 24 24"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>',
};

// UTILITY FUNCTIONS
function formatDate(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatDateTime(dateStr) {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getWeekRange() {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 7);
  return {
    start: start.toISOString().split("T")[0],
    end: end.toISOString().split("T")[0],
  };
}

function analyzeReviews(reviews) {
  const weekRange = getWeekRange();

  // Current week - NEW reviews (by published date)
  const currentWeekReviews = reviews.filter((r) => {
    const date = new Date(r.dates.publishedDate);
    return date >= new Date(weekRange.start) && date <= new Date(weekRange.end);
  });

  // Current week - UPDATED reviews
  const updatedThisWeek = reviews.filter((r) => {
    if (!r.dates.updatedDate) return false;
    const updateDate = new Date(r.dates.updatedDate);
    // Make sure it's not also counted as "new" this week
    const publishDate = new Date(r.dates.publishedDate);
    const wasNewThisWeek =
      publishDate >= new Date(weekRange.start) &&
      publishDate <= new Date(weekRange.end);
    return (
      updateDate >= new Date(weekRange.start) &&
      updateDate <= new Date(weekRange.end) &&
      !wasNewThisWeek // Don't double-count
    );
  });

  // PREVIOUS WEEK
  const prevWeekStart = new Date(weekRange.start);
  prevWeekStart.setDate(prevWeekStart.getDate() - 7);

  const prevWeekReviews = reviews.filter((r) => {
    const date = new Date(r.dates.publishedDate);
    return date >= prevWeekStart && date < new Date(weekRange.start);
  });

  // Previous week - UPDATED reviews
  const prevUpdatedReviews = reviews.filter((r) => {
    if (!r.dates.updatedDate) return false;
    const updateDate = new Date(r.dates.updatedDate);
    const publishDate = new Date(r.dates.publishedDate);
    const wasNewPrevWeek =
      publishDate >= prevWeekStart && publishDate < new Date(weekRange.start);
    return (
      updateDate >= prevWeekStart &&
      updateDate < new Date(weekRange.start) &&
      !wasNewPrevWeek
    );
  });

  // Sentiment analysis (current week new reviews only)
  const sentiment = { positive: 0, neutral: 0, negative: 0 };
  currentWeekReviews.forEach((r) => {
    if (r.rating >= 4) sentiment.positive++;
    else if (r.rating === 3) sentiment.neutral++;
    else sentiment.negative++;
  });

  // Language distribution
  const languages = {};
  currentWeekReviews.forEach((r) => {
    const lang = (r.language || "unknown").toUpperCase();
    languages[lang] = (languages[lang] || 0) + 1;
  });

  // Source distribution
  const sources = { organic: 0, verified: 0, invited: 0 };
  currentWeekReviews.forEach((r) => {
    const source = r.source?.toLowerCase() || "organic";
    if (r.labels?.verification?.isVerified) sources.verified++;
    else if (source === "invited") sources.invited++;
    else sources.organic++;
  });

  // Calculate averages
  const currentAvgRating =
    currentWeekReviews.length > 0
      ? currentWeekReviews.reduce((sum, r) => sum + r.rating, 0) /
        currentWeekReviews.length
      : 0;

  const prevAvgRating =
    prevWeekReviews.length > 0
      ? prevWeekReviews.reduce((sum, r) => sum + r.rating, 0) /
        prevWeekReviews.length
      : 0;

  // Response metrics
  const repliedReviews = currentWeekReviews.filter((r) => r.reply).length;
  const responseRate =
    currentWeekReviews.length > 0
      ? (repliedReviews / currentWeekReviews.length) * 100
      : 0;

  // Calculate avg response time
  const reviewsWithReplies = currentWeekReviews.filter((r) => r.reply);
  let avgResponseTime = 0;
  if (reviewsWithReplies.length > 0) {
    const totalDays = reviewsWithReplies.reduce((sum, r) => {
      const reviewDate = new Date(r.dates.publishedDate);
      const replyDate = new Date(r.reply.publishedDate);
      const diffDays = (replyDate - reviewDate) / (1000 * 60 * 60 * 24);
      return sum + diffDays;
    }, 0);
    avgResponseTime = totalDays / reviewsWithReplies.length;
  }

  return {
    current: {
      count: currentWeekReviews.length,
      updatedCount: updatedThisWeek.length,
      avgRating: currentAvgRating,
      sentiment,
      languages,
      sources,
      responseRate,
      repliedCount: repliedReviews,
      avgResponseTime,
      reviews: currentWeekReviews,
    },
    previous: {
      count: prevWeekReviews.length,
      updatedCount: prevUpdatedReviews.length,
      avgRating: prevAvgRating,
    },
    weekRange,
  };
}
// Analyze top mentions from backend data
function analyzeTopMentions(reviews, topMentions = []) {
  if (!topMentions || topMentions.length === 0) {
    return { positive: [], negative: [], neutral: [] };
  }

  if (!reviews || reviews.length === 0) {
    return { positive: [], negative: [], neutral: [] };
  }

  // For each topic, count how many positive vs negative reviews mention it
  const topicSentiment = {};

  topMentions.forEach((topic) => {
    topicSentiment[topic] = {
      positive: 0,
      negative: 0,
      neutral: 0,
      total: 0,
    };

    // Search for this topic in all reviews
    reviews.forEach((review) => {
      const text = (review.text || "").toLowerCase();
      const title = (review.title || "").toLowerCase();
      const searchText = text + " " + title;

      // Check if topic is mentioned (case-insensitive, partial match)
      const topicWords = topic.toLowerCase().split(" ");
      const mentioned = topicWords.some((word) => searchText.includes(word));

      if (mentioned) {
        topicSentiment[topic].total++;

        if (review.rating >= 4) {
          topicSentiment[topic].positive++;
        } else if (review.rating === 3) {
          topicSentiment[topic].neutral++;
        } else {
          topicSentiment[topic].negative++;
        }
      }
    });
  });

  // Categorize topics based on sentiment ratio
  const positive = [];
  const negative = [];
  const neutral = [];

  Object.keys(topicSentiment).forEach((topic) => {
    const sentiment = topicSentiment[topic];

    // Skip topics not mentioned this week
    if (sentiment.total === 0) {
      return;
    }

    // Categorize based on actual review sentiment
    const negativeRatio = sentiment.negative / sentiment.total;
    const positiveRatio = sentiment.positive / sentiment.total;

    if (negativeRatio > 0.6) {
      negative.push(topic);
    } else if (positiveRatio > 0.6) {
      positive.push(topic);
    } else {
      neutral.push(topic);
    }
  });

  return { positive, negative, neutral };
}

// SIMPLIFIED renderHeader() FUNCTION
// Shows "New Reviews" instead of "Total Activity"
// Replace the entire function with this:

function renderHeader(data, analytics) {
  const company = data.company;
  const weekRange = analytics.weekRange;
  const curr = analytics.current;
  const prev = analytics.previous;

  // Compare new reviews to new reviews
  const reviewChange = curr.count - prev.count;
  const reviewChangePct =
    prev.count > 0
      ? (((curr.count - prev.count) / prev.count) * 100).toFixed(1)
      : "0";

  return `
  <div class="header">
    <div class="header-row">
      <div class="brand">
        <div class="logo">
          <img src="${company.logo_url}" alt="${company.brand_name} logo">
        </div>
        <div class="brand-info">
          <h1>${company.brand_name} — Weekly Trustpilot Report</h1>
          <div class="meta">
            <span>${Icons.calendar}<strong>Period:</strong> ${formatDate(
    weekRange.start
  )} → ${formatDate(weekRange.end)}</span>
            <span>${Icons.clock}<strong>Generated:</strong> ${formatDate(
    new Date().toISOString()
  )}</span>
          </div>
        </div>
      </div>
      
      <div class="header-stats">
        <div class="stat-pill">
          <div class="label">Trust Score</div>
          <div class="value">${company.trust_score}/5</div>
          <div class="sub">Overall rating</div>
        </div>
        <div class="stat-pill">
          <div class="label">Total Reviews</div>
          <div class="value">${company.total_reviews.toLocaleString()}</div>
          <div class="sub">All-time</div>
        </div>
        <div class="stat-pill highlight">
          <div class="label">New Reviews</div>
          <div class="value">${curr.count}</div>
          <div class="sub" style="color:${
            reviewChange >= 0 ? "var(--accent)" : "var(--danger)"
          }">
            ${reviewChange >= 0 ? Icons.trendingUp : Icons.trendingDown} 
            ${reviewChange >= 0 ? "+" : ""}${reviewChangePct}% vs last week
          </div>
        </div>
      </div>
    </div>
  </div>
`;
}

// SIMPLIFIED renderHighlights() FUNCTION
// Now shows WoW comparison for BOTH new and updated reviews
// Replace the entire function with this:

function renderHighlights(analytics) {
  const curr = analytics.current;
  const prev = analytics.previous;

  const reviewChange = curr.count - prev.count;
  const reviewChangePct =
    prev.count > 0 ? ((reviewChange / prev.count) * 100).toFixed(1) : 0;

  const updatedChange = curr.updatedCount - prev.updatedCount;
  const updatedChangePct =
    prev.updatedCount > 0
      ? ((updatedChange / prev.updatedCount) * 100).toFixed(1)
      : 0;

  const ratingChange = curr.avgRating - prev.avgRating;

  return `
  <div class="highlights">
    <div class="highlights-title">
      <svg class="icon" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
      Weekly Highlights
    </div>
    <div class="highlights-grid">
      <div>
        ${Icons.edit}
        <span><strong>${curr.count} new reviews</strong> this week 
          <span style="color:${
            reviewChange >= 0 ? "var(--accent)" : "var(--danger)"
          }">
            ${reviewChange >= 0 ? "↑" : "↓"} ${Math.abs(reviewChangePct)}%
          </span>
        </span>
      </div>
      <div>
        ${Icons.refresh}
        <span><strong>${curr.updatedCount} reviews updated</strong> this week
          <span style="color:${
            updatedChange >= 0 ? "var(--accent)" : "var(--danger)"
          }">
            ${updatedChange >= 0 ? "↑" : "↓"} ${Math.abs(updatedChangePct)}%
          </span>
        </span>
      </div>
      <div>
        ${Icons.star}
        <span><strong>Avg rating:</strong> ${curr.avgRating.toFixed(2)}
          <span style="color:${
            ratingChange >= 0 ? "var(--accent)" : "var(--danger)"
          }">
            (${ratingChange >= 0 ? "+" : ""}${ratingChange.toFixed(2)})
          </span>
        </span>
      </div>
      <div>
        ${Icons.messageSquare}
        <span><strong>Response rate:</strong> ${curr.responseRate.toFixed(
          1
        )}% — ${curr.repliedCount} replies</span>
      </div>
      <div>
        ${Icons.clock}
        <span><strong>Avg response time:</strong> ${curr.avgResponseTime.toFixed(
          1
        )} days</span>
      </div>
    </div>
  </div>
`;
}

// SIMPLIFIED renderKPIs() FUNCTION
// Replaces "Total Activity" with "Updated Reviews" as separate metric
// Replace the entire function with this:

function renderKPIs(analytics) {
  const curr = analytics.current;
  const prev = analytics.previous;

  // New reviews WoW
  const reviewChange = curr.count - prev.count;
  const reviewChangePct =
    prev.count > 0 ? ((reviewChange / prev.count) * 100).toFixed(1) : 0;

  // Updated reviews WoW
  const updatedChange = curr.updatedCount - prev.updatedCount;
  const updatedChangePct =
    prev.updatedCount > 0
      ? ((updatedChange / prev.updatedCount) * 100).toFixed(1)
      : 0;

  // Avg rating WoW
  const ratingChange = curr.avgRating - prev.avgRating;
  const ratingChangePct =
    prev.avgRating > 0 ? ((ratingChange / prev.avgRating) * 100).toFixed(1) : 0;

  return `
  <div class="kpi">
    <div class="label">New Reviews</div>
    <div class="value">${curr.count}</div>
    <div class="delta ${reviewChange >= 0 ? "positive" : "negative"}">
      ${reviewChange >= 0 ? Icons.trendingUp : Icons.trendingDown}
      <span>${Math.abs(reviewChange)} (${
    reviewChange >= 0 ? "+" : ""
  }${reviewChangePct}%)</span>
    </div>
  </div>
  <div class="kpi">
    <div class="label">Updated Reviews</div>
    <div class="value">${curr.updatedCount}</div>
    <div class="delta ${updatedChange >= 0 ? "positive" : "negative"}">
      ${updatedChange >= 0 ? Icons.trendingUp : Icons.trendingDown}
      <span>${Math.abs(updatedChange)} (${
    updatedChange >= 0 ? "+" : ""
  }${updatedChangePct}%)</span>
    </div>
  </div>
  <div class="kpi">
    <div class="label">Avg Rating</div>
    <div class="value">${curr.avgRating.toFixed(2)}</div>
    <div class="delta ${ratingChange >= 0 ? "positive" : "negative"}">
      ${ratingChange >= 0 ? Icons.trendingUp : Icons.trendingDown}
      <span>${Math.abs(ratingChange).toFixed(2)} (${
    ratingChange >= 0 ? "+" : ""
  }${ratingChangePct}%)</span>
    </div>
  </div>
  <div class="kpi">
    <div class="label">Response Rate</div>
    <div class="value">${curr.responseRate.toFixed(1)}%</div>
    <div class="delta neutral">
      ${Icons.checkCircle}
      <span>${curr.repliedCount} of ${curr.count}</span>
    </div>
  </div>
  <div class="kpi">
    <div class="label">Avg Response Time</div>
    <div class="value">${curr.avgResponseTime.toFixed(1)}</div>
    <div class="delta neutral">
      ${Icons.clock}
      <span>days</span>
    </div>
  </div>
`;
}

function renderSentimentBars(sentiment, total) {
  const posPct = total > 0 ? (sentiment.positive / total) * 100 : 0;
  const neuPct = total > 0 ? (sentiment.neutral / total) * 100 : 0;
  const negPct = total > 0 ? (sentiment.negative / total) * 100 : 0;

  return `
        <div class="sentiment-item">
          <div class="sentiment-row">
            <strong>Positive (4-5 ★)</strong>
            <span>${sentiment.positive} reviews (${posPct.toFixed(1)}%)</span>
          </div>
          <div class="track">
            <div class="bar pos" style="width:${posPct}%"></div>
          </div>
        </div>
        <div class="sentiment-item">
          <div class="sentiment-row">
            <strong>Neutral (3 ★)</strong>
            <span>${sentiment.neutral} reviews (${neuPct.toFixed(1)}%)</span>
          </div>
          <div class="track">
            <div class="bar neu" style="width:${neuPct}%"></div>
          </div>
        </div>
        <div class="sentiment-item">
          <div class="sentiment-row">
            <strong>Negative (1-2 ★)</strong>
            <span>${sentiment.negative} reviews (${negPct.toFixed(1)}%)</span>
          </div>
          <div class="track">
            <div class="bar neg" style="width:${negPct}%"></div>
          </div>
        </div>
      `;
}

function renderSourcesTable(sources) {
  const total = sources.organic + sources.verified + sources.invited;
  return `
        <thead>
          <tr><th>Type</th><th style="text-align:right">Count</th><th style="text-align:right">%</th></tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="badge badge-organic">Organic</span></td>
            <td style="text-align:right">${sources.organic}</td>
            <td style="text-align:right">${
              total > 0 ? ((sources.organic / total) * 100).toFixed(1) : 0
            }%</td>
          </tr>
          <tr>
            <td><span class="badge badge-verified">Verified</span></td>
            <td style="text-align:right">${sources.verified}</td>
            <td style="text-align:right">${
              total > 0 ? ((sources.verified / total) * 100).toFixed(1) : 0
            }%</td>
          </tr>
          ${
            sources.invited > 0
              ? `
          <tr>
            <td><span class="badge badge-invited">Invited</span></td>
            <td style="text-align:right">${sources.invited}</td>
            <td style="text-align:right">${
              total > 0 ? ((sources.invited / total) * 100).toFixed(1) : 0
            }%</td>
          </tr>
          `
              : ""
          }
        </tbody>
      `;
}

function renderLanguageTable(languages) {
  const total = Object.values(languages).reduce((a, b) => a + b, 0);
  const sorted = Object.entries(languages).sort((a, b) => b[1] - a[1]);
  const top5 = sorted.slice(0, 5);

  return `
        <thead>
          <tr><th>Language</th><th style="text-align:right">Reviews</th><th style="text-align:right">%</th></tr>
        </thead>
        <tbody>
          ${top5
            .map(
              ([lang, count]) => `
            <tr>
              <td>${lang}</td>
              <td style="text-align:right"><strong>${count}</strong></td>
              <td style="text-align:right">${((count / total) * 100).toFixed(
                1
              )}%</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      `;
}

function renderTopMentions(mentions) {
  const hasPositive = mentions.positive && mentions.positive.length > 0;
  const hasNegative = mentions.negative && mentions.negative.length > 0;
  const hasNeutral = mentions.neutral && mentions.neutral.length > 0;

  // If no mentions at all
  if (!hasPositive && !hasNegative && !hasNeutral) {
    return `
          <div class="mention-box" style="grid-column: 1 / -1">
            <div class="no-data">No Trustpilot topics were mentioned in this week's reviews</div>
          </div>
        `;
  }

  return `
        <div class="mention-box">
          <div class="mention-box-title positive">
            ${Icons.thumbsUp}
            Positive Topics
            ${
              hasPositive
                ? `<span style="font-size:11px;font-weight:400;color:var(--muted);margin-left:auto">${mentions.positive.length} mentioned</span>`
                : ""
            }
          </div>
          ${
            hasPositive
              ? `
            <div class="mention-list">
              ${mentions.positive
                .map(
                  (tag) => `
                <div class="mention-tag positive">
                  ${Icons.checkCircle}
                  ${tag}
                </div>
              `
                )
                .join("")}
            </div>
          `
              : '<div class="no-data">No positive topics mentioned this week</div>'
          }
        </div>
        <div class="mention-box">
          <div class="mention-box-title negative">
            ${Icons.thumbsDown}
            Negative Topics
            ${
              hasNegative
                ? `<span style="font-size:11px;font-weight:400;color:var(--muted);margin-left:auto">${mentions.negative.length} mentioned</span>`
                : ""
            }
          </div>
          ${
            hasNegative
              ? `
            <div class="mention-list">
              ${mentions.negative
                .map(
                  (tag) => `
                <div class="mention-tag negative">
                  ${Icons.xCircle}
                  ${tag}
                </div>
              `
                )
                .join("")}
            </div>
          `
              : '<div class="no-data">No negative topics mentioned this week</div>'
          }
        </div>
        ${
          hasNeutral
            ? `
          <div class="mention-box" style="grid-column: 1 / -1">
            <div class="mention-box-title" style="color:var(--warning)">
              ${Icons.tag}
              Neutral Topics
              <span style="font-size:11px;font-weight:400;color:var(--muted);margin-left:auto">${
                mentions.neutral.length
              } mentioned</span>
            </div>
            <div class="mention-list">
              ${mentions.neutral
                .map(
                  (tag) => `
                <div class="mention-tag" style="border-color:rgba(245,158,11,0.3);background:rgba(245,158,11,0.08)">
                  ${Icons.tag}
                  ${tag}
                </div>
              `
                )
                .join("")}
            </div>
          </div>
        `
            : ""
        }
      `;
}

function renderAISummary(summary) {
  if (!summary) {
    return '<p style="color:var(--muted)">No AI summary available for this reporting period.</p>';
  }

  return `
        <p>${summary.summary}</p>
        <div class="summary-meta">
          ${Icons.clock}
          Generated: ${formatDateTime(summary.updated_at)} | Model: ${
    summary.model_version || "N/A"
  }
        </div>
      `;
}

// CHART FUNCTIONS
function createPieChart(ctx, labels, data, colors) {
  return new Chart(ctx, {
    type: "pie",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: colors,
          borderColor: "#0f1724",
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const value = context.parsed || 0;
              const total = context.dataset.data.reduce((a, b) => a + b, 0);
              const pct = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
              return `${context.label}: ${value} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

function createBarChart(ctx, labels, data) {
  return new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          data,
          backgroundColor: "rgba(0, 182, 122, 0.8)",
          borderColor: "#00b67a",
          borderWidth: 1,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
            color: "#9aa4b2",
            font: { size: 11 },
          },
          grid: {
            color: "rgba(255,255,255,0.05)",
          },
        },
        x: {
          ticks: {
            color: "#9aa4b2",
            font: { size: 11 },
          },
          grid: {
            display: false,
          },
        },
      },
    },
  });
}

// MAIN FUNCTION
async function loadAndRender() {
  try {
    let data;

    if (EMBEDDED_DATA) {
      data = EMBEDDED_DATA;
    } else {
      const response = await fetch("trustpilot_raw_data.json");
      if (!response.ok) throw new Error("Failed to load data file");
      data = await response.json();
    }

    // Analyze reviews
    const analytics = analyzeReviews(data.reviews);

    // Analyze mentions
    const mentions = analyzeTopMentions(
      analytics.current.reviews,
      data.company.top_mentions || []
    );

    // Render all sections
    document.getElementById("header").innerHTML = renderHeader(data, analytics);
    document.getElementById("highlights").innerHTML =
      renderHighlights(analytics);
    document.getElementById("kpis").innerHTML = renderKPIs(analytics);
    document.getElementById("sentimentBars").innerHTML = renderSentimentBars(
      analytics.current.sentiment,
      analytics.current.count
    );
    document.getElementById("sourcesTable").innerHTML = renderSourcesTable(
      analytics.current.sources
    );
    document.getElementById("languageTable").innerHTML = renderLanguageTable(
      analytics.current.languages
    );
    document.getElementById("mentions").innerHTML = renderTopMentions(mentions);
    document.getElementById("aiSummary").innerHTML = renderAISummary(
      data.company.ai_summary
    );

    // Create charts
    const sentCtx = document.getElementById("sentimentChart").getContext("2d");
    createPieChart(
      sentCtx,
      ["Positive (4-5★)", "Neutral (3★)", "Negative (1-2★)"],
      [
        analytics.current.sentiment.positive,
        analytics.current.sentiment.neutral,
        analytics.current.sentiment.negative,
      ],
      ["#059669", "#f59e0b", "#ff5b57"]
    );

    const srcCtx = document.getElementById("sourcesChart").getContext("2d");
    createPieChart(
      srcCtx,
      ["Organic", "Verified", "Invited"],
      [
        analytics.current.sources.organic,
        analytics.current.sources.verified,
        analytics.current.sources.invited,
      ],
      ["#3b82f6", "#059669", "#f59e0b"]
    );

    const langCtx = document.getElementById("languageChart").getContext("2d");
    const langData = Object.entries(analytics.current.languages).sort(
      (a, b) => b[1] - a[1]
    );
    createBarChart(
      langCtx,
      langData.map(([lang]) => lang),
      langData.map(([, count]) => count)
    );

    // Show report
    document.getElementById("loading").style.display = "none";
    document.getElementById("report").style.display = "block";
  } catch (error) {
    console.error("Error loading report:", error);
    document.getElementById("loading").innerHTML = `
          <div style="text-align:center;color:var(--danger)">
            <h2>Error Loading Report</h2>
            <p>${error.message}</p>
            <p style="color:var(--muted);margin-top:10px">
              Make sure 'trustpilot_raw_data.json' is in the same directory,<br>
              or embed the data directly in the EMBEDDED_DATA variable.
            </p>
          </div>
        `;
  }
}

document.addEventListener("DOMContentLoaded", loadAndRender);
