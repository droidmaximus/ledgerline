package llm

import (
	"encoding/json"
	"strings"
	"testing"
)

func TestCompactTreeOutline_IncludesSnippetTruncated(t *testing.T) {
	tree := map[string]interface{}{
		"node_id": "0001",
		"title":   "Root",
		"summary": "R",
		"text":    strings.Repeat("A", 2000),
		"nodes": []interface{}{
			map[string]interface{}{
				"node_id":      "0002",
				"title":        "Fin",
				"summary":      "Revenue",
				"start_index":  float64(3),
				"end_index":    float64(5),
				"text":         strings.Repeat("B", 2000),
				"nodes":        []interface{}{},
			},
		},
	}
	b, err := CompactTreeOutline(tree, 400)
	if err != nil {
		t.Fatal(err)
	}
	var arr []map[string]interface{}
	if err := json.Unmarshal(b, &arr); err != nil {
		t.Fatal(err)
	}
	if len(arr) == 0 {
		t.Fatal("expected non-empty outline")
	}
	// snippetMaxRunes in code is 800; allow some slack for ellipsis characters.
	for _, row := range arr {
		sn, _ := row["snippet"].(string)
		if sn == "" {
			t.Fatalf("expected snippet for node row: %v", row)
		}
		if len([]rune(sn)) > 810 {
			t.Fatalf("snippet should be truncated; len runes=%d snippet=%q", len([]rune(sn)), sn)
		}
	}
}

func TestCompactTreeOutline_TruncatesLongSummary(t *testing.T) {
	long := make([]rune, 500)
	for i := range long {
		long[i] = 'x'
	}
	tree := map[string]interface{}{
		"node_id": "0001",
		"title":   "R",
		"summary": string(long),
		"nodes":   []interface{}{},
	}
	b, err := CompactTreeOutline(tree, 100)
	if err != nil {
		t.Fatal(err)
	}
	var arr []map[string]interface{}
	if err := json.Unmarshal(b, &arr); err != nil {
		t.Fatal(err)
	}
	if len(arr) != 1 {
		t.Fatalf("expected 1 outline row, got %d", len(arr))
	}
	s, _ := arr[0]["summary"].(string)
	if len([]rune(s)) > 110 {
		t.Fatalf("summary should be truncated, len runes=%d", len([]rune(s)))
	}
}
