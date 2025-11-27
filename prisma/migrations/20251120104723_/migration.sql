/*
  Warnings:

  - You are about to drop the column `gamesLost` on the `Team` table. All the data in the column will be lost.
  - You are about to drop the column `gamesPlayed` on the `Team` table. All the data in the column will be lost.
  - You are about to drop the column `gamesTied` on the `Team` table. All the data in the column will be lost.
  - You are about to drop the column `gamesWon` on the `Team` table. All the data in the column will be lost.
  - You are about to drop the column `goalDifference` on the `Team` table. All the data in the column will be lost.
  - You are about to drop the column `goalsAgainst` on the `Team` table. All the data in the column will be lost.
  - You are about to drop the column `goalsFor` on the `Team` table. All the data in the column will be lost.
  - You are about to drop the column `points` on the `Team` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "Team" DROP COLUMN "gamesLost",
DROP COLUMN "gamesPlayed",
DROP COLUMN "gamesTied",
DROP COLUMN "gamesWon",
DROP COLUMN "goalDifference",
DROP COLUMN "goalsAgainst",
DROP COLUMN "goalsFor",
DROP COLUMN "points";
