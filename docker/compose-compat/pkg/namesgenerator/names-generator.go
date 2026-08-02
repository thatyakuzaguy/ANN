package namesgenerator

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"time"
)

// GetRandomName returns a collision-resistant local builder name.
func GetRandomName(retry int) string {
	var value [8]byte
	if _, err := rand.Read(value[:]); err == nil {
		return fmt.Sprintf("ann-builder-%s-%d", hex.EncodeToString(value[:]), retry)
	}
	return fmt.Sprintf("ann-builder-%d-%d", time.Now().UnixNano(), retry)
}
